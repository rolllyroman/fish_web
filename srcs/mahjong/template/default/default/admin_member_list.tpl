<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/common.js"></script>
      <div class="block">
                %include admin_frame_header
                <div class="content">
                    %include search
                    <table id="dataTable" class="table table-bordered table-hover"></table>
                </div>
</div>
<script type="text/javascript">
    var pageNumber;
    $('#btn_search').click(function(){
          $('#dataTable').bootstrapTable('refresh');
    });

    $('#dataTable').bootstrapTable({
          method: 'get',
          url: '{{info["listUrl"]}}',
          contentType: "application/json",
          datatype: "json",
          cache: false,
          striped: true,
          toolbar:'#toolbar',
          pagination: true,
          pageSize: 15,
          pageNumber:parseInt("{{info['cur_page']}}"),
          pageList: [15, 50, 100],
          queryParamsType:'',
          sidePagination:"server",
          minimumCountColumns: 2,
          clickToSelect: true,
          //smartDisplay: true,
          responseHandler:responseFun,
          queryParams:getSearchP,
          onSort:getCellSortByClick,
          //sortOrder: 'asc',
          //sortable: true,                     //是否启用排序
          // exportOptions:{fileName: "{{info['title']}}"+"_"+ new Date().Format("yyyy-MM-dd")},
          columns: [
          [
                {
                    "halign":"center",
                    "align":"center",
                    "class":'count',
                    "colspan": 12
                }
          ],

          [{
              field: 'id',
              title: '用户编号',
              align: 'center',
              valign: 'middle',
              sortable: true
          },{
              field: 'name',
              title: '用户名称',
              align: 'center',
              valign: 'middle'
          },{
              field: 'nickname',
              title: '微信名称',
              align: 'center',
              valign: 'middle'
          },{
              field: 'headImgUrl',
              title: '微信头像',
              align: 'center',
              valign: 'middle',
              formatter:getAvatorImg,
          },{
              field: 'parentAg',
              title: '公会号',
              align: 'center',
              valign: 'middle',
              sortable: true
          },{
              %if info.has_key('fish'):
                  field : 'coin',
                  title : '金币剩余',
              %else:
                  field : 'roomcard',
                  title : '钻石剩余',
              %end
              align: 'center',
              valign: 'middle',
              sortable: true,
          }
          %if info.has_key('fish'):
                  ,{
                      field: 'exchange_ticket',
                      title: '剩余兑换券',
                      align: 'center',
                      valign: 'middle',
                      sortable: true,
                  }
          %end
          ,{
              field: 'last_login_date',
              title: '最近登录时间',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'last_logout_date',
              title: '最近登出时间',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              %if info.has_key('fish'):
                  field: 'recharge_coin_total',
                  title: '历史金币充值总额',
              %else:
                  field: 'rechargeTotal',
                  title:'充值总额(当前公会)',
              %end
              align: 'center',
              valign: 'middle',
              sortable: true,
          }
          %if not info.has_key("fish"):
              ,{
                  field: 'open_auth',
                  title: '代开权限<br/>(仅权限代开模式生效)',
                  align: 'center',
                  valign: 'middle',
                  sortable: true,
                  formatter:status
              }
          %end
          ,{
              field: 'valid',
              title: '状态',
              align: 'center',
              valign: 'middle',
              sortable: true,
              formatter:is_valid
          },{
              field: 'op',
              title: '操作',
              align: 'center',
              valign: 'middle',
              formatter:getOp
          }]]
    });

      function status(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          var statusstr = '';
          if(rowobj['open_auth'] == '1'){
              statusstr = '<span class="label label-success">是</span>';
          }else if(rowobj['open_auth'] == '0'){
              statusstr = '<span class="label label-danger">否</span>';
          }

          return [
              statusstr
          ].join('');
      }

      function is_valid(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          var statusstr = '';
          if(rowobj['valid'] == '1'){
              statusstr = '<span class="label label-success">正常</span>';
          }else if(rowobj['valid'] == '0'){
              statusstr = '<span class="label label-danger">冻结</span>';
          }

          return [
              statusstr
          ].join('');
      }

      function getCellSortByClick(name,sort){ //用于服务端排序重写

          console.log(String.format('------getCellSortByClick name[{0}] sort[{1}]',name,sort));
          $('#dataTable').bootstrapTable('refresh',{'url':String.format('{0}&sort_name={1}&sort_method={2}','{{info["listUrl"]}}',name,sort)});
      }

      function getOp(value,row,index){
          var comfirmUrls = [
              '/admin/member/kick',
              '/admin/member/freeze/fish',
              '/admin/member/freeze/hall',
              '/admin/member/open_auth'
          ];

          var notShowOp = [
                '/admin/member/open_auth',
                '/admin/member/modify',
          ];

          eval('rowobj='+JSON.stringify(row))
          var opList = []
          for (var i = 0; i < rowobj['op'].length; ++i) {
              var op = rowobj['op'][i];
              var str = JSON.stringify({id : rowobj['id'],cur_size:"{{info['cur_size']}}",cur_page:pageNumber});
              var cStr = str.replace(/\"/g, "@");
              %if info.has_key('fish'):
                  if (notShowOp.indexOf(op['url'])>=0){
                      continue;
                  }
              %end
              if(comfirmUrls.indexOf(op['url'])>=0)
                  opList.push(String.format("<a href=\"#\" class=\"btn btn-primary btn-sm\" onclick=\"comfirmDialog(\'{0}\', \'{1}\', \'{2}\')\">{3}</a> ", op['url'], op['method'], cStr, op['txt']));
              else
                  opList.push(String.format("<a href=\"{0}/{5}?id={1}&page_size={2}&cur_page={3}\" class=\"btn btn-primary btn-sm\" > {4} </a> ", op['url'],rowobj['id'],"{{info['cur_size']}}",pageNumber,op['txt'],"{{info['remove_type']}}"));
          }
          return opList.join('');
      }

      //定义列操作
      function getSearchP(p){
        var searchId = $("#searchId").val();
        console.log(p);
        sendParameter = p;
        sendParameter['searchId'] = searchId;

        return sendParameter;
      }

      function responseFun(res){
          count= res.total;
          //实时刷
          $('.count').text(String.format("会员总人数:{0}",count));
          pageNumber = parseInt(res.pageNumber);
          return {"rows": res.result,
                  "total": res.total
          };
      }

      function responseError(status) {
          location.reload();
      }
</script>
%rebase admin_frame_base
