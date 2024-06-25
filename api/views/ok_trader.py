import time
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class TraderDataView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        now = int(time.time()) * 1000
        try:
            # 当前持仓
            url1 = f'https://www.okx.com/priapi/v5/ecotrade/public/positions-v2?limit=10&uniqueName=563E3A78CDBAFB4E&t={now}'
            positions_data = requests.get(url1).json().get("data", [{}])[0].get("posData", [])

            # 历史持仓
            url2 = f'https://www.okx.com/priapi/v5/ecotrade/public/history-positions?limit=10&uniqueName=563E3A78CDBAFB4E&t={now}'
            history_data = requests.get(url2).json().get("data", [])

            return Response({
                'positions_data': positions_data,
                'history_data': history_data
            }, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
