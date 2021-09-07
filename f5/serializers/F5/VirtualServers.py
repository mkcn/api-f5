from rest_framework import serializers


class F5VirtualServersSerializer(serializers.Serializer):
    class F5VirtualServersInnerSerializer(serializers.Serializer):
        class F5VirtualServersItemsSerializer(serializers.Serializer):
            class F5VirtualServersPoolReferenceSerializer(serializers.Serializer):
                link = serializers.CharField(max_length=255, required=True)

            class F5VirtualServersSourceAddressTranslationSerializer(serializers.Serializer):
                type = serializers.CharField(max_length=255, required=True)

            class F5VirtualServersSecurityLogProfilesReferenceSerializer(serializers.Serializer):
                link = serializers.CharField(max_length=255, required=True)

            class F5VirtualServersPersistSerializer(serializers.Serializer):
                class F5VirtualServersPersistNameReferenceSerializer(serializers.Serializer):
                    link = serializers.CharField(max_length=255, required=True)

                name = serializers.CharField(max_length=255, required=True)
                partition = serializers.CharField(max_length=255, required=True)
                tmDefault = serializers.CharField(max_length=255, required=True)
                nameReference = F5VirtualServersPersistNameReferenceSerializer(required=True)

            class F5VirtualServersReferenceSerializer(serializers.Serializer):
                link = serializers.CharField(max_length=255, required=True)
                isSubcollection = serializers.BooleanField(required=True)

            name = serializers.CharField(max_length=255, required=True)
            partition = serializers.CharField(max_length=255, required=True)
            fullPath = serializers.CharField(max_length=255, required=True)
            generation = serializers.IntegerField(required=True)
            selfLink = serializers.CharField(max_length=255, required=True)
            addressStatus = serializers.CharField(max_length=255, required=True)
            autoLasthop = serializers.CharField(max_length=255, required=True)
            cmpEnabled = serializers.CharField(max_length=255, required=True)
            connectionLimit = serializers.IntegerField(required=True)
            creationTime = serializers.CharField(max_length=255, required=True)
            destination = serializers.CharField(max_length=255, required=True)
            enabled = serializers.BooleanField(required=False)
            gtmScore = serializers.IntegerField(required=True)
            ipProtocol = serializers.CharField(max_length=255, required=True)
            lastModifiedTime = serializers.CharField(max_length=255, required=True)
            mask = serializers.CharField(max_length=255, required=True)
            mirror = serializers.CharField(max_length=255, required=True)
            mobileAppTunnel = serializers.CharField(max_length=255, required=True)
            nat64 = serializers.CharField(max_length=255, required=True)
            pool = serializers.CharField(max_length=255, required=False)
            poolReference = F5VirtualServersPoolReferenceSerializer(required=False)
            rateLimit = serializers.CharField(max_length=255, required=False)
            rateLimitDstMask = serializers.IntegerField(required=True)
            rateLimitMode = serializers.CharField(max_length=255, required=False)
            rateLimitSrcMask = serializers.IntegerField(required=True)
            serviceDownImmediateAction = serializers.CharField(max_length=255, required=False)
            source = serializers.CharField(max_length=255, required=False)
            sourceAddressTranslation = F5VirtualServersSourceAddressTranslationSerializer(required=True)
            sourcePort = serializers.CharField(max_length=255, required=True)
            synCookieStatus = serializers.CharField(max_length=255, required=True)
            translateAddress = serializers.CharField(max_length=255, required=True)
            translatePort = serializers.CharField(max_length=255, required=True)
            vlansDisabled = serializers.BooleanField(required=False)
            vsIndex = serializers.IntegerField(required=True)
            securityLogProfiles = serializers.ListField(
                child=serializers.CharField(max_length=255, required=True),
                required=False
            )
            securityLogProfilesReference = F5VirtualServersSecurityLogProfilesReferenceSerializer(many=True, required=False)
            persist = F5VirtualServersPersistSerializer(many=True, required=False)
            policiesReference = F5VirtualServersReferenceSerializer(required=True)
            profilesReference = F5VirtualServersReferenceSerializer(required=True)


        items = F5VirtualServersItemsSerializer(many=True)

    data = F5VirtualServersInnerSerializer(required=True)