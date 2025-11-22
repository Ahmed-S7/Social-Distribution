"""
Remote post receiver view.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import RemotePost
from ..serializers import RemotePostSerializer


class RemotePostReceiver(APIView):
    def post(self, request):
        serializer = RemotePostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "received"})
        return Response(serializer.errors, status=400)

