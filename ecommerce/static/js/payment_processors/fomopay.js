/**
 * FOMO Pay payment processor specific actions.
 */
require([
    'jquery',
], function ($) {
    'use strict';

    $(document).ready(function () {

        var order_id = window.PaymentConfig.order_id;
        var url = window.PaymentConfig.status_url;

        Spinner();
        Spinner.show();
        setTimeout(poll, 10000);

        function poll() {
            $.get(url, { order_id: order_id })
                .done(function (data) {
                    console.log(data);
                    if (data['status'] !== 'success') {
                        setTimeout(poll, 10000);
                    } else {
                        Spinner.hide();
                        $('#continue').css( "display", "block" )
                    }
                });
        }
    });

    // Loading Spinner
    // [Demo](https://zulns.github.io/LoadingSpinner.js/)
    function Spinner() {
        Spinner.element = document.getElementById('spinner');
        Spinner.label = document.getElementById('label-spinner');
        let c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
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
        document.body.appendChild(Spinner.element)
    }
    Spinner.id = null;
    Spinner.label = null;
    Spinner.element = null;
    Spinner.show = function () {
        const c = 264, m = 15;
        Spinner.element.style.display = 'block';
        move1();
        function move1() {
            let i = 0, o = 0;
            move();
            function move() {
                if (i == c) move2();
                else {
                    i += 4; o += 8;
                    Spinner.element.setAttribute('stroke-dasharray', i + ' ' + (c - i));
                    Spinner.element.setAttribute('stroke-dashoffset', o)
                    Spinner.id = setTimeout(move, m)
                }
            }
        }
        function move2() {
            let i = c, o = c * 2;
            move();
            function move() {
                if (i == 0) move1();
                else {
                    i -= 4; o += 4;
                    Spinner.element.setAttribute('stroke-dasharray', i + ' ' + (c - i));
                    Spinner.element.setAttribute('stroke-dashoffset', o)
                    Spinner.id = setTimeout(move, m)
                }
            }
        }
    };
    Spinner.hide = function () {
        Spinner.element.style.display = 'none';
        Spinner.label.style.display = 'none';
        if (Spinner.id) {
            clearTimeout(Spinner.id);
            Spinner.id = null
        }
        Spinner.element.setAttribute('stroke-dasharray', '0 264');
        Spinner.element.setAttribute('stroke-dashoffset', '0')
    };


});
