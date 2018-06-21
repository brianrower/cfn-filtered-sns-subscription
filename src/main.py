import os
import logging
import cfn_filtered_sns_subscription_provider

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))


def handler(request, context):
    if request['ResourceType'] == 'Custom::FilteredSNSSubscription':
        return cfn_filtered_sns_subscription_provider.handler(request, context)
