<style type="text/css">.config-table td.table-title{text-align:center;font-size:13px;vertical-align:middle}</style>
<div class='block'>
          %include admin_frame_header
          <div class="content" id="sign_app">
             <form class="form-horizontal group-border-dashed" id='addform' @submit.prevent="onSubmit" :action="action" method="post" style="border-radius: 0px;" enctype="multipart/form-data">
               <input type="hidden" name="sign_id" :value="signId">
               <table class='table config-table'>
                        <tr>
                              <td>
                                <table class='table config-table' border='1'>
                                    <tr>
                                         <td class='table-title'>配置标题</td>
                                         <td>
                                             <input type="text" style='width:100%;float:left' id="title" name="title" :value="signData.title" class="form-control">
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>第一天</td>
                                         <td>
                                             <h5>奖励类型:</h5>
                                             <div v-for="type in types" >
                                                <input type="radio" :checked="type.checked" :value="type.give_type" name="day1_type"/>${type.text}
                                             </div>
                                             <br/>
                                             <h5>奖励数额:</h5>
                                             <input type="text" style='width:100%;float:left' id="day1" name="day1" :value="signData.day1.coin" class="form-control">
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>第二天</td>
                                         <td>
                                             <h5>奖励类型:</h5>
                                             <div v-for="type in types" >
                                                <input type="radio" :checked="type.checked" :value="type.give_type" name="day2_type"/>${type.text}
                                             </div>
                                             <br/>
                                             <input type="text" style='width:100%;float:left' id="day2" name="day2" :value="signData.day2.coin" class="form-control">
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>第三天</td>
                                         <td>
                                             <h5>奖励类型:</h5>
                                             <div v-for="type in types" >
                                                <input type="radio" :checked="type.checked" :value="type.give_type" name="day3_type"/>${type.text}
                                             </div>
                                             <br/>
                                             <input type="text" style='width:100%;float:left' id="day3" name="day3" :value="signData.day3.coin" class="form-control">
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>第四天</td>
                                         <td>
                                             <h5>奖励类型:</h5>
                                             <div v-for="type in types" >
                                                <input type="radio" :checked="type.checked" :value="type.give_type" name="day4_type"/>${type.text}
                                             </div>
                                             <br/>
                                             <input type="text" style='width:100%;float:left' id="day4" name="day4" :value="signData.day4.coin" class="form-control">
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>第五天</td>
                                         <td>
                                             <h5>奖励类型:</h5>
                                             <div v-for="type in types" >
                                                <input type="radio" :checked="type.checked" :value="type.give_type" name="day5_type"/>${type.text}
                                             </div>
                                             <br/>
                                             <input type="text" style='width:100%;float:left' id="day5" name="day5" :value="signData.day5.coin" class="form-control">
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>第六天</td>
                                         <td>
                                             <h5>奖励类型:</h5>
                                             <div v-for="type in types" >
                                                <input type="radio" :checked="type.checked" :value="type.give_type" name="day6_type"/>${type.text}
                                             </div>
                                             <br/>
                                             <input type="text" style='width:100%;float:left' id="day6" name="day6" :value="signData.day6.coin" class="form-control">
                                         </td>
                                    </tr>
                                    <tr>
                                         <td class='table-title'>第七天</td>
                                         <td>
                                             <h5>奖励类型:</h5>
                                             <div v-for="type in types" >
                                                <input type="radio" :checked="type.checked" :value="type.give_type" name="day7_type"/>${type.text}
                                             </div>
                                             <br/>
                                             <input type="text" style='width:100%;float:left' id="day7" name="day7" :value="signData.day6.coin" class="form-control">
                                         </td>
                                    </tr>
                                </table>
                              </td>
                        </tr>
              </table>
              <div class="modal-footer" style="text-align:center">
                   <button type="submit" class="btn btn-primary">{{lang.BTN_SUBMIT_TXT}}</button>
                  <button type="button" class="btn btn-primary" @click.prevent="onBack">{{lang.BTN_BACK_TXT}}</button>
              </div>
            </form>
    </div>
</div>
<script type="text/javascript">
    var sign_app = new Vue({
        el: '#sign_app',
        data:{
            types: [
                 {'give_type':1,'text':'金币','checked':true}
            ],
            signId: "{{sign_id}}",
            action: "{{info['submitUrl']}}",
            signData: {{!sign_data}}
        },
        methods: {
            onSubmit: function(){
                 formAjax($('#addform').attr("action"), $('#addform').attr("method"), $('#addform').serialize(),'正在创建...');
            },
            onBack: function(){
                window.location.href="{{info['backUrl']}}";
            }
        },delimiters:['${','}']
    });
    console.log(sign_app.signData)
</script>
%rebase admin_frame_base
