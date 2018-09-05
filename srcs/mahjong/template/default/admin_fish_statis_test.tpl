  <div class='block'>
       %include admin_frame_header
       <div class='content'>
          <div id="toolbar" class="btn-group">
               <button id="btn_add" type="button" class="btn btn-sm btn-primary">
                  <span class="glyphicon glyphicon-plus">
                      <a href="{{info['createUrl']}}" style='color:#FFF;text-decoration:none;'>调试预设值</a>
                  </span>
              </button>

               <button id="btn_add" type="button" class="btn btn-sm btn-primary">
                  <span class="glyphicon glyphicon-plus">
                      <a href="/admin/fish/statis" style='color:#FFF;text-decoration:none;'>总玩入玩出统计</a>
                  </span>
              </button>

			  <!--
               <button id="clear_all" type="button" class="btn btn-sm btn-primary">
                  <span class="glyphicon glyphicon-plus">
                      <a href="/admin/fish/clear/statis" style='color:#FFF;text-decoration:none;'>清零当前统计数据</a>
                  </span>
              </button>
			  -->
          </div>
          <table id='loadDataTable' class="table table-bordered table-hover " ></table>
       </div>
  </div>
<script type="text/javascript">
    /**
      *表格数据
    */
    var editId;        //定义全局操作数据变量
    var isEdit;
    var startDate;
    var endDate;
    $('#loadDataTable').bootstrapTable({
          method: 'get',
          url: "{{info['tableUrl']}}",
          contentType: "application/json",
          datatype: "json",
          cache: false,
          checkboxHeader: true,
          detailView: true,//父子表
          pagination: true,
          pageSize: 16,
          toolbar:'#toolbar',
          pageList: [24, 48, 100,'All'],
          search: true,
          showRefresh: true,
          minimumCountColumns: 2,
          clickToSelect: true,
          smartDisplay: true,
          //sidePagination : "server",
          sortOrder: 'desc',
          sortName: 'datetime',
          //queryParams:getSearchP,
          responseHandler:responseFunc,
          //onLoadError:responseError,
          showExport:true,
          exportTypes:['excel', 'csv', 'pdf', 'json'],
          //exportOptions:{fileName: "{{info['title']}}"+"_"+ new Date().Format("yyyy-MM-dd")},
          columns: [
          [{
                    halign    : "center",
                    font      :  15,
                    align     :  "left",
                    class     :  "totalTitle",
                    colspan   :  12
          }],
          [{
              checkbox: true
          },{
              field: 'uid',
              title: '用户id',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{

              field: 'cost_coin_sum',
              title: '总消耗',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{

              field: 'gain_coin_sum',
              title: '总获得',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{

              field: 'play_in_sum',
              title: '总玩入',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{
              field: 'play_out_sum',
              title: '总玩出',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{
              field: 'cur_rate',
              title: '当前比例',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{
              field: 'pre_rate',
              title: '预设比例',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{
              field: 'above_rate',
              title: '比例以上捕获率',
              align: 'center',
			  sortable:true,
              valign: 'middle'
		  },{
              field: 'under_rate',
              title: '比例以下捕获率',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{
              field: 'play_difference_value',
              title: '玩入玩出清零差值',
              align: 'center',
			  sortable:true,
              valign: 'middle'
          },{
			  field: 'op',
              title: '操作',
              align: 'center',
              valign: 'middle',
              formatter:getOp	
          }]],

         //注册加载子表的事件。注意下这里的三个参数！
          onExpandRow: function (index, row, $detail) {
              console.log(index,row,$detail);
              //InitSubTable(index, row, $detail);
          }
      });

        function responseFunc(res){
            data = res.data;
            //count = res.count;
            z_cost = res.z_cost;
            z_gain = res.z_gain;
            z_play_in = res.z_play_in;
            z_play_out = res.z_play_out;
            $('.totalTitle').html('用户总消耗:'+z_cost+"&nbsp;&nbsp;&nbsp;&nbsp;用户总获得:"+z_gain+'&nbsp;&nbsp;&nbsp;&nbsp;用户总玩入:'+z_play_in+"&nbsp;&nbsp;&nbsp;&nbsp;用户总玩出:"+z_play_out);
            return data;
        }

		function getOp(value,row,index){
          eval('var rowobj='+JSON.stringify(row))

          res = "<a href='/admin/fish/clear/statis/test?uid="+rowobj['uid']+"' class='btn btn-primary'>清零玩入玩出数据</a>"

          return [
            res
          ].join('');
      }


</script>
%rebase admin_frame_base
