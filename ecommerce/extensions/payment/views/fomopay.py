"""FOMO Pay payment processing views."""

import base64
import logging
import StringIO

import qrcode
import requests
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View


from ecommerce.extensions.payment.processors.fomopay import Fomopay

logger = logging.getLogger(__name__)


class FomopayQRView(View):
    """Starts FOMO Pay payment process.

    This view acts as an interface between the user and FOMO Pay,
    it'll mainly display the QR code and instructions on how to make a payment with the WeChat app.
    """

    # Disable CSRF validation. The internal POST requests to render this view
    # don't include the CSRF token as hosted-side payment processor are
    # excepted to be externally hosted, but this is not the case.
    # Instead of changing the checkout flow for all the payment processors
    # this view is marked as exempt.
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(FomopayQRView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        """ Render QR Code.

        Process the incoming request to render the QR in the template.
        """
        qr_url = self._get_qr_link(request)
        qr_img = self._generate_qr(qr_url)
        context = {'qrcode': qr_img}

        return render(request, 'payment/fomopay.html', context)

    def _generate_qr(self, qr_url):
        """
        Create a base64 representation of the QR code image.
        """
        img = qrcode.make(qr_url)
        img_io = StringIO.StringIO()
        img.save(img_io, format='PNG')

        return base64.b64encode(img_io.getvalue())

    def _get_qr_link(self, request):
        """
        Process the outgoing request to the FOMO API to obtain the
        link needed to create the QR code
        """
        params = request.POST.dict()
        api_url = params.pop('api_url')
        response = requests.post(url=api_url, data=params)
        fomo_response = response.json()
        qr_url = fomo_response.get('url')

        return qr_url


class FomopayPaymentResponseView(View):
    pass
