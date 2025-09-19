"""
Application layer views - to be configured later

Raw data import is handled by Airflow DAGs → TimescaleDB (direct SQL)
Application views will be configured later for business features.
"""

# Application layer views will be configured later
# Raw data import is handled by Airflow DAGs → TimescaleDB directly

from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from users.auth import APIKeyAuthentication, IsAirflowService, StaffTokenObtainPairView
from .models import SwitchRequest, SwitchStatus, RegistryMessage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class SwitchUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SwitchStatus.choices)
    nt_sent_at = serializers.DateTimeField(required=False)

class UpdateSwitchStatusView(generics.UpdateAPIView):
    queryset = SwitchRequest.objects.all()
    serializer_class = SwitchUpdateSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated, IsAirflowService]
    lookup_field = 'id'

    def perform_update(self, serializer):
        instance = self.get_object()
        instance.status = serializer.validated_data['status']
        if 'nt_sent_at' in serializer.validated_data:
            instance.nt_sent_at = serializer.validated_data['nt_sent_at']
        instance.save()

class RegistryMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryMessage
        fields = '__all__'

class RegistryMessageView(generics.CreateAPIView):
    queryset = RegistryMessage.objects.all()
    serializer_class = RegistryMessageSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated, IsAirflowService]

class ManualActionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, id):
        try:
            switch_request = SwitchRequest.objects.get(id=id)
        except SwitchRequest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        switch_request.override_active = True
        switch_request.override_reason = request.data.get('reason', 'No reason provided.')
        switch_request.save()

        # TODO: Trigger the manual_file_generator_dag
        # from .tasks import trigger_manual_file_generator_dag
        # trigger_manual_file_generator_dag.delay(
        #     switch_request_id=switch_request.id,
        #     action=request.data.get('action'),
        #     payload=request.data.get('payload')
        # )

        return Response(status=status.HTTP_202_ACCEPTED)
