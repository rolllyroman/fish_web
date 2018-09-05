<div class="block">
          %include admin_frame_header
          <form class="form-inline definewidth m10"  style='padding: 19px 29px 29px;' action="{{info['searchUrl']}}" method="get">
            <div class='row'>
                <div class='col-sm-12'>
                    <p align='center'>
                      <span style='font-size:22px;font-weight:600;'>{{info['title']}}</span>
                    </p>
                </div>
                <div class='col-sm-12'>
                    <p align='center'><input type='text' name='memberId' style='width:200px;height:35px;' placeholder="请输入玩家编号" value="{{info['memberId']}}" />&nbsp;</p>
                </div>
                <div class='col-sm-12'>
                     <p align='center'><input type='submit' style='width:200px;height:35px;' value='充值' class='btn btn-sm btn-primary' /></p>
                </div>
                %if message:
                <p align='center'>
                      <span style='color:red'>{{message}}</span>
                </p>
                %end
            </div>
          </form>
  </div>
%rebase admin_frame_base
