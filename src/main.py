import os
import logging
import cfn-filtered-sns-subscription-provider

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))


def handler(request, context):
    if request['ResourceType'] == 'Custom::FilteredSNSSubscription':
        return cfn-filtered-sns-subscription-provider.handler(request, context)
