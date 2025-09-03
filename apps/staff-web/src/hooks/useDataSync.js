import { useCallback, useRef, useEffect } from 'react';
import { dataSyncManager } from '../utils/dataSync';
import { saveOnboardingStep } from '../services/onboarding';

const MAX_BATCH_SIZE = 5; // Maximum number of steps to sync in one batch
const MIN_SYNC_INTERVAL = 5000; // Minimum time between syncs

export function useDataSync({ onSyncStatusChange } = {}) {
  const syncManager = useRef(dataSyncManager);
  const syncInProgress = useRef(false);
  const pendingSyncSteps = useRef(new Map());
  const lastSyncTime = useRef(null);
  const syncAttempts = useRef(new Map()); // Track sync attempts per step
  const lastSyncAttempt = useRef(0);

  // Cleanup function
  const cleanup = useCallback(() => {
    pendingSyncSteps.current.clear();
    syncInProgress.current = false;
    syncAttempts.current.clear();
  }, []);

  // Sync function
  const syncData = useCallback(async () => {
    if (syncInProgress.current) {
      return;
    }

    const now = Date.now();
    if (now - lastSyncAttempt.current < MIN_SYNC_INTERVAL) {
      return;
    }

    lastSyncAttempt.current = now;
    syncInProgress.current = true;
    
    try {
      const stepsToSync = Array.from(pendingSyncSteps.current.entries());
      pendingSyncSteps.current.clear();
      
      if (stepsToSync.length > 0) {
        try {
          // Update sync status to saving
          onSyncStatusChange?.({
            status: 'saving',
            pendingUpdates: stepsToSync.length
          });

          // Group steps into batches
          const batches = [];
          for (let i = 0; i < stepsToSync.length; i += MAX_BATCH_SIZE) {
            batches.push(stepsToSync.slice(i, i + MAX_BATCH_SIZE));
          }

          // Process each batch
          for (const batch of batches) {
            // Sync all steps in this batch
            await Promise.all(batch.map(async ([key, data]) => {
              const attempts = syncAttempts.current.get(key) || 0;
              
              // Skip if we've tried too many times
              if (attempts >= 3) {
                return;
              }

              try {
                await saveOnboardingStep(key, data, true);
                lastSyncTime.current = new Date().toISOString();
                syncAttempts.current.delete(key); // Reset attempts on success
                
                // Update sync status for this step
                onSyncStatusChange?.({
                  status: 'saving',
                  stepKey: key,
                  lastSyncTime: lastSyncTime.current,
                  pendingUpdates: stepsToSync.length - 1
                });

                // Trigger step completion check
                syncManager.current.checkStepCompletion(key, data);
              } catch (error) {
                // Log the error for debugging
                console.error('Failed to sync data:', error);
                // Update sync status
                if (onSyncStatusChange) {
                  onSyncStatusChange({
                    status: 'error',
                    stepKey: key,
                    error: error.message
                  });
                }
              }
            }));
          }

          // Update final sync status
          onSyncStatusChange?.({
            status: 'saved',
            lastSyncTime: lastSyncTime.current,
            pendingUpdates: pendingSyncSteps.current.size
          });
        } catch (error) {
          // Update sync status
          onSyncStatusChange?.({
            status: 'error',
            error: error.message,
            pendingUpdates: pendingSyncSteps.current.size
          });
        }
      }
    } finally {
      syncInProgress.current = false;
    }
  }, [onSyncStatusChange]);

  // Queue sync function (no debounce)
  const queueSync = useCallback((stepKey, stepData) => {
    // Add timestamp to data
    const timestampedData = {
      ...stepData,
      lastModified: new Date().toISOString(),
      needsSync: true
    };

    // Update local storage
    const currentData = syncManager.current.getLocalData() || {};
    const updatedLocal = {
      ...currentData,
      [stepKey]: timestampedData
    };
    syncManager.current.setLocalData(updatedLocal);

    // Queue for sync
    pendingSyncSteps.current.set(stepKey, timestampedData);

    // Directly trigger sync (no debounce)
    syncData();

    return timestampedData;
  }, [syncData]);

  // Expose dataSyncManager methods
  const getLocalData = useCallback(() => {
    return syncManager.current.getLocalData();
  }, []);

  const setLocalData = useCallback((data) => {
    return syncManager.current.setLocalData(data);
  }, []);

  const mergeData = useCallback((localData, backendData) => {
    return syncManager.current.mergeData(localData, backendData);
  }, []);

  // Add event listener for step completion
  useEffect(() => {
    const handleStepCompletionUpdate = (event) => {
      const { completionStatus } = event.detail;
      onSyncStatusChange?.({
        status: 'saved',
        completionStatus,
        lastSyncTime: lastSyncTime.current
      });
    };

    syncManager.current.addEventListener('stepCompletionUpdate', handleStepCompletionUpdate);
    return () => {
      syncManager.current.removeEventListener('stepCompletionUpdate', handleStepCompletionUpdate);
    };
  }, [onSyncStatusChange]);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return {
    queueSync,
    cleanup,
    lastSyncTime: lastSyncTime.current,
    getLocalData,
    setLocalData,
    mergeData
  };
} 