<!DOCTYPE html>
<html>
    <head>
        <title>{{title}}</title>
        <style type="text/css">
            *{margin:0;padding:0;}
            html,body{
                height: 100%;
                width: 100%;
                position: absolute;
            }
            #wrap{
                        width:100%;
                        height:100%;
                        /**
                        background-size:100% 100%;
                        background:url("/intro/banner-bg-max.png");
                        background-repeat: no-repeat;
                        background-size:100% 100%;
                        /**/
                        box-shadow: #001020 0px 0px 18px inset;
                        overflow-y: auto;
            }
            .wrap-content{
                    padding:8px;
            }
        </style>
    </head>
    <body>
        <div id='wrap'>
             <div class="wrap-content">
                 {{!content}}
             </div>
        </div>
    </body>
</html>