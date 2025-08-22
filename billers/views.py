from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.response import Response


class BankListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            branch = request.user.profile.branch.id
            bank_list = BankDetail.objects.all()
            if branch:
                billers = Biller.objects.filter(branch_id = branch).values_list('id')
                bank_list = bank_list.filter(biller_id__in = billers)

            # biller = request.get('biller_id', None)
            # print(biller)
            # if biller:
            #     bank_list = bank_list.filter(biller_id=biller)

            serializer = BankDetailSerializer(bank_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

