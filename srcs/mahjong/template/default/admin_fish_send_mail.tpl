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


	<!--
        <div class="form-group">
            <label class="col-sm-5 control-label">邮件标题</label>
            <div class="col-sm-6">
                  <input type='text' style='width:100%;float:left' name='title' class="form-control" >
            </div>
       </div>

	-->	
       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">是否发送给所有用户（1为是 否则不填）</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='send_all'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">接收用户id</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='uid'  data-rules="{required:true}" class="form-control">
            </div>
       </div>


        %for item in items:
       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">{{item["title"]}}(发送数量，没有则不填)</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='{{item["field"]}}'  data-rules="{required:true}" class="form-control">
            </div>
       </div>
        %end

       <div class="modal-footer" style="text-align:center">
           <button type="submit" class="btn btn-sm btn-xs btn-primary btn-mobile">确认发送</button>
       </div>


</form>
</div>
</div>
</div>
%rebase admin_frame_base

<script>

    if("{{post_res}}"=="1"){
        alert("发送成功！")
    }else if("{{post_res}}"=="2"){
        alert("发送失败！")
    }
</script>
