// IE8+ compatible demo site script

$(function () {

    var $text = $('#text');

    var $infobar = $('#infobar');

    var sentence = $('#sentence').text();
    var startChar, endChar;

    // var lastSelection;


    var positionInfobar = function () {
        var selectionInfo = lightrange.getSelectionInfo();


        var positionTop = $("#sentence").position().top - $(window).scrollTop();
        var positionBottom = positionTop + $('#sentence').height();

        // console.log(positionTop, selectionInfo.yStart, positionBottom, selectionInfo.yEnd)
        if (positionTop <= selectionInfo.yStart && positionBottom >= selectionInfo.yEnd) {
            startChar = selectionInfo.charStart;
            endChar = selectionInfo.charEnd;
            while (sentence.charAt(startChar) == " ") {
                startChar += 1;
            }
            while ((sentence.charAt(startChar - 1) != " ") && (startChar != 0)) {
                startChar -= 1;
            }
            while (sentence.charAt(endChar - 1) == " ") {
                endChar -= 1;
            }
            while ((sentence.charAt(endChar) != " ") && (endChar != sentence.length)) {
                endChar += 1;
            }
            $text.text(sentence.slice(startChar, endChar));
        } else {
            $text.text('');
        }
        // console.log(startChar + " is the final start.");
        // $text.text(selectionInfo.text);
    };


    // $('body').on('mouseup', function () {
    //     positionInfobar();
    //     // $infobar.addClass('active');
    // });
    // $('body, main').on('scroll', function () {
    //     positionInfobar();
    // });
    // $(window).on('resize', function () {
    //     positionInfobar();
    // });

    $('#save-selection').on('click', function (event) {
        // lastSelection = lightrange.saveSelection();
        positionInfobar();
        console.log(startChar, endChar);

        $("[id^=offset]").each(function () {

            var offset_id = $(this).attr('id');
            console.log(parseInt(offset_id.slice(6)), startChar);
            $("#offset_min").val(startChar);
            $("#offset_max").val(endChar);
            if(parseInt(offset_id.slice(6))>endChar || parseInt(offset_id.slice(6))<startChar) {
                $(this).hide();
            } else {
                $(this).show();
            }
        });

        // Preventing from display empty infobar if clicked at start
        event.stopPropagation();
    });


    $('.main-button').on('click', function (event) {
        // Preventing from display empty infobar if clicked at start
        event.stopPropagation();
    });

});
