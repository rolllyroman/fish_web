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
                  <input type='text' style='width:100%;float:left' name='item_id' class="form-control" value="{{item_id}}" readonly="readonly">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具名称</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='title'  value="{{title}}" data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">道具描述</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='des'  value="{{des}}" data-rules="{required:true}" class="form-control">
            </div>
       </div>


       <div class="modal-footer" style="text-align:center">
           <button type="submit" class="btn btn-sm btn-xs btn-primary btn-mobile">修改</button>
       </div>


</form>
</div>
</div>
</div>
%rebase admin_frame_base
