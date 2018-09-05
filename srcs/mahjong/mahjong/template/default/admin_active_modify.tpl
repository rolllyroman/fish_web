<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/fileInput/js/fileinput.min.js"></script>
<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/fileInput/js/locales/zh.js"></script>
<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/fileInput/ds_file_upload.js"></script>
<div class="block">
          %include admin_frame_header
          <div class="content">
             <form class='form-horizontal group-border-dashed' action="{{info['submitUrl']}}" method='POST' id='noticeForm' onSubmit='return false'>
              <input type="hidden" name='activeId' value="{{info['activeId']}}" />
              <div class="form-group">
                 <label class="col-sm-3 control-label">
                    活动标题
                    <br/>
                    <small>活动标题内容</small>
                 </label>
                 <div class='col-sm-7'>
                       <input type="text" name="title" class="form-control" style="width:100%;height:40px;" value="{{active_info['title']}}">
                 </div>
              </div>
              <div class="form-group">
                 <label class="col-sm-3 control-label">
                    排序值
                    <br/>
                    <small>从小到大拍</small>
                 </label>
                 <div class='col-sm-7'>
                       <input type="text" name="sort" class="form-control" style="width:100%;height:40px;" value="{{active_info['sort']}}">
                 </div>
              </div>
              <div class="form-group">
                  <label class="col-sm-3 control-label">
                     活动标签图1
                     <br/>
                     <small>活动标签点击前图</small>
                  </label>
                 <div class='col-sm-7'>
                       <img src="{{active_info['imgPath1']}}" width="200" height="100" title="" />
                       <input type="file" name="files" id="func_file" multiple class="file-loading" />
                       <input type="hidden" name="imgPath1" id="imgPath1" value="{{active_info['imgPath1']}}"/>
                       <input type="hidden" name="imgPath1_old" id="imgPath1_old" value="{{active_info['imgPath1']}}"/>
                 </div>
              </div>

              <div class="form-group">
                  <label class="col-sm-3 control-label">
                     活动标签图2
                     <br/>
                     <small>活动标签点击后切换图</small>
                  </label>
                 <div class='col-sm-7'>
                       <img src="{{active_info['imgPath2']}}" width="200" height="100" title="" />
                       <input type="file" name="files" id="func_file1" multiple class="file-loading" />
                       <input type="hidden" name="imgPath2" id="imgPath2" value="{{active_info['imgPath2']}}"/>
                       <input type="hidden" name="imgPath2_old" id="imgPath2_old" value="{{active_info['imgPath2']}}"/>
                 </div>
              </div>

              <div class="form-group">
                 <label class="col-sm-3 control-label">
                    活动内容图
                    <br/>
                    <small>活动点击后内容展示图</small>
                 </label>
                 <div class='col-sm-7'>
                       <img src="{{active_info['imgPath3']}}" width="200" height="100" title="" />
                       <input type="file" name="files" id="func_file2" multiple class="file-loading" />
                       <input type="hidden" name="imgPath3" id="imgPath3" value="{{active_info['imgPath3']}}"/>
                       <input type="hidden" name="imgPath3_old" id="imgPath3_old" value="{{active_info['imgPath3']}}"/>
                 </div>
              </div>

              <div class="modal-footer" style="text-align:center">
                   <button type="submit" class="btn btn-sm btn-primary">{{lang.BTN_SUBMIT_TXT}}</button>
                   <button type="button" class="btn btn-sm btn-primary" name="backid" id="backid">{{lang.BTN_BACK_TXT}}</button>
              </div>
            </form>
          </div>
</div>


<script type="text/javascript">
       $('#backid').click(function(){
           window.location.href="{{info['backUrl']}}";
      });

       $('#noticeForm').submit(function(){
             formAjax($(this).attr("action"), $(this).attr("method"), $(this).serialize(),'正在创建...');
       });

       //0.初始化fileinput
      var oFileInput = new FileInput();
      oFileInput.Init("func_file",  "{{info['upload_url']}}");
      oFileInput.Init("func_file1", "{{info['upload_url']}}");
      oFileInput.Init("func_file2", "{{info['upload_url']}}");
</script>
%rebase admin_frame_base
