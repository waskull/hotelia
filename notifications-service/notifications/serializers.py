from rest_framework import serializers

class EmailSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=200)
    body = serializers.CharField()
    destinations = serializers.ListField(
        child=serializers.EmailField()
    )