<div class='block'>
        %include admin_frame_header
        <div class='content' id="remove_app1">
            <form class='form-horizontal group-border-dashed' @submit="onSubmit" action="{{info['submitUrl']}}" method='POST' id='removeCard' onSubmit='return false' >
                  <input type='hidden' name='agentId' value="{{info['agentId']}}" />
                  <input type='hidden' name='memberId' value="{{info['memberId']}}" />

                   <div class="form-group">
                        <label class="col-sm-5 col-xs-10 control-label" v-if="page=='cards'">会员钻石数:</label>
                        <label class="col-sm-5 col-xs-10 control-label" v-if="page=='coin'">会员金币数:</label>
                        <div class="col-sm-6 col-xs-12">
                              <input type='text'  value="{{info['roomcard']}}" readonly='' style='width:100%;float:left' name='roomcard' data-rules="{required:true}"  class="form-control">
                        </div>
                   </div>

                   <div class="form-group">
                        <label class="col-sm-5 col-xs-10 control-label" v-if="page=='cards'" >移除的钻石数:</label>
                        <label class="col-sm-5 col-xs-10 control-label" v-if="page=='coin'"  >移除的金币数:</label>
                        <div class="col-sm-6 col-xs-12">
                              <input type='text'  style='width:100%;float:left' name='remove' data-rules="{required:true}"  class="form-control">
                        </div>
                   </div>

                   <div class="modal-footer" style="text-align:center">
                       <button type="submit" class="btn btn-sm btn-xs btn-primary btn-mobile">确定</button>
                       <button type="button" class="btn btn-sm btn-xs btn-primary btn-mobile" name="backid" @click="onBack">返回</button>
                   </div>
            </form>
        </div>
</div>
<script type="text/javascript">
    $(function(){
            var remove_app = new Vue({
                    el : '#remove_app1',
                    data : {
                        'page' : ''
                    },mounted:function(){
                        this.$data.page = "{{page}}";
                    },methods:{
                        onSubmit:function(e){
                            e.preventDefault();
                            formAjax($('#removeCard').attr("action"), $('#removeCard').attr("method"), $('#removeCard').serialize(),'正在移除...');
                        },
                        onBack:function(e){
                            e.preventDefault();
                            window.location.href="{{info['backUrl']}}";
                        }
                    }
            });
    });
</script>
%rebase admin_frame_base
