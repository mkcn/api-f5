from rest_framework import serializers


class F5KeysSerializer(serializers.Serializer):
    class F5KeysInnerSerializer(serializers.Serializer):
        class F5KeysItemsSerializer(serializers.Serializer):
            name = serializers.CharField(max_length=255, required=True)
            fullPath = serializers.CharField(max_length=65535, required=True)
            generation = serializers.IntegerField(required=True)
            selfLink = serializers.CharField(max_length=65535, required=True)
            keySize = serializers.IntegerField(required=True)
            keyType = serializers.CharField(max_length=65535, required=True)
            securityType = serializers.CharField(max_length=65535, required=True)

        items = F5KeysItemsSerializer(many=True)

    data = F5KeysInnerSerializer(required=True)