jQuery(document).ready(function($){
    var alertHeight = 0;
    $('.100vh-ignore-headers').each(function(){ 
        $('.alert').each(function(){ 
            alertHeight += $(this).outerHeight(true);
        });
        $(this).css({
            'margin-top' : document.documentElement.clientHeight/2 - (alertHeight+$(this).outerHeight()) + 'px' 
        });
    });
    $('.alert').on('closed.bs.alert', function () {
        $('.100vh-ignore-headers').each(function(){ 
            $(this).css({
                'margin-top' : parseFloat($(this).css("marginTop")) + alertHeight + 'px' 
            });
        });
    })
});

