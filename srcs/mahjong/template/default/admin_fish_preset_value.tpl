<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/agent_create.js"></script>
<div class="cl-mcont">
    <div class='block'>
         <div class='header'>
             <h3>调整预设值</h3>
         </div>
<div class='content'>
      <form class='form-horizontal group-border-dashed' action="{{info['submitUrl']}}" method='POST'  >

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">预设比例</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='preset_value' value='{{preset_value}}'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">比例之下的捕获率</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='down_chance' value='{{down_chance}}'  data-rules="{required:true}" class="form-control">
            </div>
       </div>


       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">比例之上的捕获率</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='up_chance' value='{{up_chance}}'  data-rules="{required:true}" class="form-control">
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">玩入玩出清零值</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='diff_value' value='{{diff_value}}'  data-rules="{required:true}" class="form-control">
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
