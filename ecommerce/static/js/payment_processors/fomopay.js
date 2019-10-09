
/**
 * FOMO Pay payment processor specific actions.
 */
/* eslint no-use-before-define: 0 */
require([
    'jquery'
], function($) {
    'use strict';

    // Loading Spinner
    // [Demo](https://zulns.github.io/LoadingSpinner.js/)
    function Spinner() {
        var c;
        Spinner.element = document.getElementById('spinner');
        Spinner.label = document.getElementById('label-spinner');
        c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        Spinner.element.setAttribute('width', '100');
        Spinner.element.setAttribute('height', '100');
        c.setAttribute('viewBox', '0 0 100 100');
        c.setAttribute('cx', '50');
        c.setAttribute('cy', '50');
        c.setAttribute('r', '42');
        c.setAttribute('stroke-width', '16');
        c.setAttribute('stroke', '#2196f3');
        c.setAttribute('fill', 'transparent');
        Spinner.element.appendChild(c);
        document.body.appendChild(Spinner.element);
    }
    Spinner.id = null;
    Spinner.label = null;
    Spinner.element = null;
    Spinner.show = function() {
        var c = 264;
        var m = 15;
        Spinner.element.style.display = 'block';
        move1();
        function move1() {
            var i = 0;
            var o = 0;
            move();
            function move() {
                if (i === c) move2();
                else {
                    i += 4; o += 8;
                    Spinner.element.setAttribute('stroke-dasharray', i + ' ' + (c - i));
                    Spinner.element.setAttribute('stroke-dashoffset', o);
                    Spinner.id = setTimeout(move, m);
                }
            }
        }
        function move2() {
            var i = c;
            var o = c * 2;
            move();
            function move() {
                if (i === 0) move1();
                else {
                    i -= 4; o += 4;
                    Spinner.element.setAttribute('stroke-dasharray', i + ' ' + (c - i));
                    Spinner.element.setAttribute('stroke-dashoffset', o);
                    Spinner.id = setTimeout(move, m);
                }
            }
        }
    };
    Spinner.hide = function() {
        Spinner.element.style.display = 'none';
        Spinner.label.style.display = 'none';
        if (Spinner.id) {
            clearTimeout(Spinner.id);
            Spinner.id = null;
        }
        Spinner.element.setAttribute('stroke-dasharray', '0 264');
        Spinner.element.setAttribute('stroke-dashoffset', '0');
    };

    $(document).ready(function() {
        var orderID = window.PaymentConfig.order_id;
        var url = window.PaymentConfig.status_url;

        Spinner();
        Spinner.show();
        setTimeout(poll, 10000);

        function poll() {
            $.get(url, {order_id: orderID})
                .done(function(data) {
                    if (data.status === 'success') {
                        Spinner.hide();
                        $('#continue').css('display', 'block');
                    } else if (data.status === 'error') {
                        Spinner.hide();
                        $('#error').css('display', 'block');
                    } else {
                        setTimeout(poll, 10000);
                    }
                });
        }
    });
});
