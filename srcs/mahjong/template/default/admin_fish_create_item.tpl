<div class="cl-mcont">
    <div class='block'>
         <div class='header'>
             <h3>
             %if info.get('title',None):
               {{info['title']}}
             %end
           </h3>
         </div>
<div class='content'>
      <form class='form-horizontal group-border-dashed' action="{{info['submitUrl']}}" method='POST' id='selfModify'>
       <div class="form-group">
            <label class="col-sm-5 control-label">道具id</label>
            <div class="col-sm-6">
                  <input type='text' style='width:100%;float:left' name='item_id' class="form-control" >
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具名称</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='title'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具描述</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='des'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

	<!--

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具价格</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='price'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具有效次数</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='times'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具有效天数</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='days'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具单位(填0为个 1为元)</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='unit'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">是否可兑奖(0为不可 1为可兑)</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='can_reward'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

-->

       <div class="modal-footer" style="text-align:center">
           <button type="submit" class="btn btn-sm btn-xs btn-primary btn-mobile">创建</button>
       </div>


</form>
</div>
</div>
</div>
%rebase admin_frame_base

<script>
    if("{{post_res}}"=="1"){
        alert("创建失败！")
    }else if("{{post_res}}"=="2"){
        alert("创建失败！请填写完整道具信息！")
    }else if("{{post_res}}"=="3"){
        alert("创建失败！道具id重复！")
    }
</script>
