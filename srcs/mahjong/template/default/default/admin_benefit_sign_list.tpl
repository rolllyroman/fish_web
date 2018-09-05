<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/common.js"></script>
<div class="block">
          %include admin_frame_header
          <div class="content">
              <div class="toolbar">
                     <button class='btn btn-primary btn-sm' onclick="addHandler()">
                             {{info['addTitle']}}
                     </button>
              </div>
              <table id="dataTable" class="table table-bordered table-hover"></table>
          </div>
</div>
<script>
function addHandler(){
    window.location.href="{{info['createUrl']}}";
}
</script>
<script type="text/javascript">
  /**
    * 服务端刷新表格
    --------------------------------------------
  */
  $(function () {

      $('#dataTable').bootstrapTable({
          method:'get',
          url   :'{{info["listUrl"]}}',
          smartDisplay: true,
          pagination: true,
          pageSize: 15,
          pageList: [15,50,100,'All'],
          responseHandler:responseFunc,
          columns: [
                    [{
                        field: 'title',
                        title: '标题',
                        align: 'center',
                        valign: 'middle',
                        formatter:function(value,row,index){
                            return '<font color="#1E9FFF">'+value+'</font>';
                        }
                    },{
                        field: 'day1',
                        title: '第一天',
                        align: 'center',
                        valign: 'middle',
                        formatter:getDatas
                    },{
                        field: 'day2',
                        title: '第二天',
                        align: 'center',
                        valign: 'middle',
                        formatter:getDatas
                    },{
                        field: 'day3',
                        title: '第三天',
                        align: 'center',
                        valign: 'middle',
                        formatter:getDatas
                    },{
                        field: 'day4',
                        title: '第四天',
                        align: 'center',
                        valign: 'middle',
                        formatter:getDatas
                    },{
                        field: 'day5',
                        title: '第五天',
                        align: 'center',
                        valign: 'middle',
                        formatter:getDatas
                    },{
                        field: 'day6',
                        title: '第六天',
                        align: 'center',
                        valign: 'middle',
                        formatter:getDatas
                    },{
                        field: 'day7',
                        title: '第七天',
                        align: 'center',
                        valign: 'middle',
                        formatter:getDatas
                    },{
                        field: 'status',
                        title: '状态',
                        align: 'center',
                        valign: 'middle',
                        formatter: function(value,row,index){
                            if (value == '1'){
                                return '<label class="label label-sm label-success">进行中</label>';
                            }else{
                                return '<label class="label label-sm label-warning">等待中</label>';
                            }
                        }
                    },{
                        field: 'op',
                        title: '操作',
                        align: 'center',
                        valign: 'middle',
                        formatter: getOp
                    }]
         ]
      });

      function getOp(value,row,index){
          eval('rowobj='+JSON.stringify(row));
          showComfirUrl = [
                '/admin/benefit/sign/open',
                '/admin/benefit/sign/remove'
          ];
          var opList = []
          for (var i = 0; i < rowobj['op'].length; ++i) {
              var op = rowobj['op'][i];
              var str = JSON.stringify({sign_id : rowobj['id']});
              var cStr = str.replace(/\"/g, "@");
              if(showComfirUrl.indexOf(op['url'])>-1){
                  opList.push(String.format("<a href=\"#\" class=\"btn btn-primary btn-sm\" onclick=\"comfirmDialog(\'{0}\', \'{1}\', \'{2}\')\"><i class=\"glyphicon glyphicon-edit\"> {3} </i></a> ", op['url'], op['method'], cStr, op['txt']));
              }else{
                  opList.push(String.format("<a href=\"{0}?sign_id={1}\" class=\"btn btn-primary btn-sm\"><i class=\"glyphicon glyphicon-edit\"> {2}</i></a> ", op['url'], rowobj['id'], op['txt']));
              }
          }
          return opList.join('');
      }

      function getDatas(value,row,index){
          eval('rowobj='+JSON.stringify(row))
          if (value.give_type == '1')
              return '金币x'+value.coin;
      }


      function responseFunc(res){
          data = res.data;
          count= res.count;

          return data;
      }
  });
</script>
%rebase admin_frame_base
