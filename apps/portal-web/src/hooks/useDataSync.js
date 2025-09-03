import { useCallback, useRef, useEffect } from 'react';
import { dataSyncManager } from '../utils/dataSync';
import { saveOnboardingStep } from '../services/onboarding';

const MAX_BATCH_SIZE = 5; // Maximum number of steps to sync in one batch
const MIN_SYNC_INTERVAL = 2000; // Minimum time between syncs (reduced from 5s to 2s)

export function useDataSync({ onSyncStatusChange } = {}) {
  const syncManager = useRef(dataSyncManager);
  const syncInProgress = useRef(false);
  const pendingSyncSteps = useRef(new Map());
  const lastSyncTime = useRef(null);
  const syncAttempts = useRef(new Map()); // Track sync attempts per step
  const lastSyncAttempt = useRef(0);
  const inFlightRequests = useRef(new Set());


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
      
      if (stepsToSync.length > 0) {
        // Only clear pending steps after we've successfully copied them
        pendingSyncSteps.current.clear();
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
              // Skip if a request for this key is already in flight
              if (inFlightRequests.current.has(key)) {
                return;
              }
              
              const attempts = syncAttempts.current.get(key) || 0;
              
              // Skip if we've tried too many times
              if (attempts >= 3) {
                return;
              }

              try {
                // Add to in-flight requests
                inFlightRequests.current.add(key);

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
                
                // Re-add failed sync back to pending if it's not a permanent error
                if (attempts < 2) {
                  syncAttempts.current.set(key, attempts + 1);
                  pendingSyncSteps.current.set(key, data);
                }
                
                // Update sync status
                if (onSyncStatusChange) {
                  onSyncStatusChange({
                    status: 'error',
                    stepKey: key,
                    error: error.message
                  });
                }
              } finally {
                // Remove from in-flight requests
                inFlightRequests.current.delete(key);
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