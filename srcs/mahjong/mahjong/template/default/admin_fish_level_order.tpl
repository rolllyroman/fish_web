<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/refreshDateInit.js"></script>
<div class="block">
          %include admin_frame_header
          </div>
          <div class="content">
             <table id="dataTable" class="table table-bordered table-hover"></table>
          </div>
</div>
<script type="text/javascript">

  /**------------------------------------------------
    *  代理操作日志
    *
    -------------------------------------------------
  */
  function initTable() {

    $('#dataTable').bootstrapTable({
          method: 'get',
          url: '{{info["listUrl"]}}',
          contentType: "application/json",
          datatype: "json",
          cache: false,
          checkboxHeader: true,
          striped: true,
          showExport: true,
          pagination: true,
          pageSize: 24,
          pageList: [12, 48, 100, 'All'],
          search: true,
          showColumns: true,
          showRefresh: true,
          minimumCountColumns: 2,
          clickToSelect: true,
          smartDisplay: true,
          //sidePagination : "server",
          queryParams:getSearchP,
          responseHandler:responseFun,
          //onLoadError:responseError,
          showExport:true,
          //rtTypes:['excel', 'csv', 'pdf', 'json'],
          // exportOptions:{fileName: "{{info['title']}}"+"_"+ new Date().Format("yyyy-MM-dd")},
          columns: [
          {
              field: 'order',
              title: 'orderId',
              align: 'center',
              valign: 'middle'
          },{
              field: 'name',
              title: '名称',
              align: 'center',
              valign: 'middle'
          },{
              field: 'op',
              title: '操作',
              align: 'center',
              valign: 'middle',
              formatter:getOp
          }]
      });

        //定义列操作
        function getSearchP(p){
          startDate = $("#pick-date-start").val();
          endDate   = $("#pick-date-end").val();

          sendParameter = p;

          sendParameter['startDate'] = startDate;
          sendParameter['endDate']  = endDate;

          return sendParameter;
        }

        function getOp(value,row,index){
            eval('rowobj='+JSON.stringify(row))
            var opList = []
            for (var i = 0; i < rowobj['op'].length; ++i) {
                var op = rowobj['op'][i];
                var str = JSON.stringify({id : rowobj['account']});
                var cStr = str.replace(/\"/g, "@");

                opList.push(String.format("<a href=\"{0}\" class=\"btn btn-primary btn-sm\" >{1}</a> ", op['url'],op['txt']));
            }
            return opList.join('');
        }

        //获得返回的json 数据
        function responseFun(res){
            data = res;
            return data;
        }
}
</script>
%rebase admin_frame_base