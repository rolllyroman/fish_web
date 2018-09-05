<style type="text/css">.config-table td.table-title{text-align:center;font-size:13px;vertical-align:middle}</style>
<div class="block">
          %include admin_frame_header
          <div class="content" id='good_app'>
             <form class="form-horizontal group-border-dashed" id='gameForm' v-on:submit="onSubmit" action="{{info['submitUrl']}}" method="post" style="border-radius: 0px;" enctype="multipart/form-data">
               <input type="hidden" name="goodsId" v-bind:value="goodId" />
               <input type="hidden" name="goods_type" v-bind:value="goodsInfo.type" />
                   <table class='table config-table'>
                        <tr>
                          <td width='20%' class='table-title'>编辑商品</td>
                        </tr>
                        <tr>
                              <td class='table-title'>`</td>
                              <td>
                                <table class='table config-table' border='1'>
                                    <tr>
                                         <td class='table-title'>商品名称</td>
                                         <td>
                                             <input type="text" style='width:100%;float:left' v-model="goodsInfo.name" v-bind:value="goodsInfo.name" id="name" name="name" class="form-control">
                                             <label for='name' class='hitLabel' style='float:left;line-height:30px'>*</label>
                                         </td>
                                    </tr>

                                    <tr>
                                        <td class='table-title' v-if="system == 'HALL'">{{lang.GOODS_CARD_TXT}}</td>
                                        <td class='table-title' v-if="system == 'FISH'">{{lang.GOODS_COIN_TXT}}</td>
                                         <td>
                                             <input type="text" style='width:100%;float:left' v-bind:value="goodsInfo.cards" id="cards" name="cards" class="form-control">
                                             <label for='cards' class='hitLabel' style='float:left;line-height:30px'>*</label>
                                         </td>
                                    </tr>
                                     <tr>
                                         <td class='table-title' v-if="system=='HALL'">{{lang.GOODS_CARD_PRESENT_TXT}}</td>
                                         <td class='table-title' v-if="system=='FISH'">{{lang.GOODS_COIN_PRESENT_TXT}}</td>
                                         <td>
                                             <input type="text" style='width:100%;float:left' v-bind:value="goodsInfo.present_cards" id="present_cards" name="present_cards" class="form-control">
                                             <label for='present_cards' class='hitLabel' style='float:left;line-height:30px'>*</label>
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>商品价格(单位:元)</td>
                                         <td>
                                             <input type="text" style='width:100%;float:left' v-bind:value="goodsInfo.price" id="price" name="price" class="form-control">
                                             <label for='price' class='hitLabel' style='float:left;line-height:30px'>*</label>
                                         </td>
                                    </tr>
                        </tr>
                  </table>
                  <div class="modal-footer" style="text-align:center">
                       <button type="submit" class="btn btn-primary">{{lang.BTN_SUBMIT_TXT}}</button>
                       <button type="button" class="btn btn-primary" v-on:click="onClick">{{lang.BTN_BACK_TXT}}</button>
                  </div>
            </form>
          </div>
</div>

<script type="text/javascript">

    function initPage(results){  //渲染页面
        var good_app = new Vue({
                 el   :   '#good_app'
                ,data : {
                    goodsInfo :  results.goods_info,
                    goodId    :  '',
                    action    :  '',
                    system    :  ''
                },mounted: function() {
                   var self = this;
                   self.$data.goodsInfo = results.goods_info;
                   self.$data.goodId = "{{goodsId}}";
                   self.$data.action =  "{{info['submitUrl']}}";
                   self.$data.system = "{{system}}";

               },methods:{
                   onSubmit:function(e) {
                        e.preventDefault();
                        formAjax($('#gameForm').attr("action"), $('#gameForm').attr("method"), $('#gameForm').serialize(),'正在修改...');
                   },
                   onClick : function(e){
                       e.preventDefault();
                       window.location.href="{{info['backUrl']}}";
                   }
               },delimiters: ['${', '}']

        });

    }

    $(function() {  //获取数据接口
        var api = String.format("/admin/goods/info/{0}",{{goodsId}});
        $.getJSON(api,function (results) {
            initPage(results);
        });
    });


</script>
%rebase admin_frame_base
