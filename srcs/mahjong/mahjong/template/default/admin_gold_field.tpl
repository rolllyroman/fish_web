<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/common.js"></script>
<div class="block">
         %include admin_frame_header
          <div class="content">
                <table id="goldTable" class="table table-bordered table-hover"></table>
          </div>
</div>
<script type="text/javascript">

    function getSearchP(p){
        var search = $("#searchId").val();
        sendParameter = p;
        sendParameter['search'] = search;

        return sendParameter;
    }

    function get_bds(value,row,index){
        href = row['buy_diamond_stream']
        value = value || 0;
        return "<a href='"+href+"'>" + value + "</a>"
    }

    function get_bgs(value,row,index){
        href = row['buy_gold_stream']
        value = value || 0;
        return "<a href='"+href+"'>" + value + "</a>"
    }

    function get_grs(value,row,index){
        href = row['gold_record_stream']
        return "<a href='"+href+"'>跳转</a>"
    }

    function get_sbr(value,row,index){
        href = row['store_buy_record']
        return "<a href='"+href+"'>跳转购买流水</a>"
    }


    $("#goldTable").bootstrapTable({
            url: '{{info["listUrl"]}}',
            method: 'get',
            pagination: true,
            pageSize: 15,
            sortOrder: 'desc',
            search:true,
            sortName: 'regDate',
            sorttable:true,
            responseHandler:responseFunc,
            queryParams:getSearchP,
            showExport:true,
            exportTypes:['excel', 'csv', 'pdf', 'json'],
            pageList: '{{PAGE_LIST}}',
            columns:[
            [{
                    halign    : "center",
                    font      :  15,
                    align     :  "left",
                    class     :  "totalTitle",
                    colspan   :  19, 
            }],
            [
            {
                field: 'uid',
                title: 'UID',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'account',
                sortable: true,
                title: '微信账号',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'nickname',
                title: '昵称',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'phone_num',
                title: '手机号',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'agent',
                sortable: true,
                title: '所属公会',
                align: 'center',
                valign: 'middle',
            },{

                field: 'agent_wealth_rank',
                sortable: true,
                title: '公会财富排名',
                align: 'center',
                valign: 'middle',
            },{

                field: 'gold_win_rate',
                title: '金币场胜率',
                valign: 'middle',
                align: 'center',
                valign:'middle',
                sortable: true,
            },{

                field: 'agent_win_rank',
                title: '公会胜局榜排名',
                align: 'center',
                valign: 'middle',
                sortable: true,
                valign:'middle'
            },{

                field: 'cur_diamond_num',
                title: '当前钻石数',
                valign: 'middle',
                align: 'center',
                valign:'middle',
                sortable: true,
            },{

                field: 'buy_diamond_num',
                title: '购买钻石金额',
                valign: 'middle',
                align: 'center',
                sortable: true,
                formatter:get_bds,
            },{

                field: 'sbr',
                title: '商城购买记录',
                align: 'center',
                valign: 'middle',
                formatter:get_sbr
            },{

                field: 'cur_gold_num',
                title: '当前金币数',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'buy_gold_num',
                title: '购买金币金额',
                align: 'center',
                valign: 'middle',
                sortable: true,
                formatter:get_bgs,
            },{

                field: 'join_gold_game_sum',
                title: '参与金币场游戏总局数',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'grs',
                title: '金币战绩流水',
                align: 'center',
                valign: 'middle',
                formatter:get_grs
            },{

                field: 'first_log_date',
                title: '首次登陆时间',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'last_log_date',
                title: '最后登录时间',
                align: 'center',
                valign: 'middle',
                sortable: true,
            }]],
            //注册加载子表的事件。注意下这里的三个参数！
            onExpandRow: function (index, row, $detail) {
                console.log(index,row,$detail);
                InitSubTable(index, row, $detail);
            }
    });




//初始化子表格
function InitSubTable(index, row, $detail) {
        var parentAg = row.parentId;
        var cur_table = $detail.html('<table table-bordered table-hover definewidth style="margin-left:55px;background:#EEEEE0"></table>').find('table');
        $(cur_table).bootstrapTable({
                url: '{{info["listUrl"]}}',
                method: 'get',
                contentType: "application/json",
                datatype: "json",
                cache: false,
                search: true,
                sorttable:true,
                toolbar:'#toolbar',
                showRefresh: true,
                clickToSelect: true,
                smartDisplay: true,
                queryParams:getSearchP,
                sortOrder: 'desc',
                sortName: 'regDate',
                pageSize: 15,
                pageList: [15, 25],
                columns: [
            {
                field: 'uid',
                title: 'UID',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'weixin',
                sortable: true,
                title: '微信账号',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'nick_name',
                title: '昵称',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'phone_num',
                title: '手机号',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'agent',
                sortable: true,
                title: '所属公会',
                align: 'center',
                valign: 'middle',
            },{

                field: 'agent_wealth_rank',
                sortable: true,
                title: '公会财富排名',
                align: 'center',
                valign: 'middle',
            },{

                field: 'gold_win_rate',
                title: '金币场胜率',
                valign: 'middle',
                align: 'center',
                valign:'middle',
                sortable: true,
            },{

                field: 'agent_win_rank',
                title: '公会胜局榜排名',
                align: 'center',
                valign: 'middle',
                sortable: true,
                valign:'middle'
            },{

                field: 'cur_diamond_num',
                title: '当前钻石数',
                valign: 'middle',
                align: 'center',
                valign:'middle',
                sortable: true,
            },{

                field: 'buy_diamond_num',
                title: '购买钻石金额',
                valign: 'middle',
                align: 'center',
                sortable: true,
                formatter:get_bds,
            },{

                field: 'sbr',
                title: '商城购买记录',
                align: 'center',
                valign: 'middle',
                formatter:get_sbr
            },{

                field: 'cur_gold_num',
                title: '当前金币数',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'buy_gold_num',
                title: '购买金币金额',
                align: 'center',
                valign: 'middle',
                sortable: true,
                formatter:get_bgs,
            },{

                field: 'join_gold_game_sum',
                title: '参与金币场游戏总局数',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'grs',
                title: '金币战绩流水',
                align: 'center',
                valign: 'middle',
                formatter:get_grs
            },{

                field: 'first_log_date',
                title: '首次登陆时间',
                align: 'center',
                valign: 'middle',
                sortable: true,
            },{

                field: 'last_log_date',
                title: '最后登录时间',
                align: 'center',
                valign: 'middle',
                sortable: true,
            }],
                //注册加载子表的事件。注意下这里的三个参数！
                onExpandRow: function (index, row, $detail) {
                    console.log(index,row,$detail);
                    InitSubTable(index, row, $detail);
                }
        });



        function responseFunc(res){
            data = res.data;
            count= res.count;
            //实时刷

            return data;
        }

}


function responseFunc(res){
    data = res.data;
    count= res.count;
    //实时刷

    // $('.totalTitle').html("下线代理总数: "+count)

    return data;
}


String.format = function() {
    if( arguments.length == 0 ) {
    return null;
    }
    var str = arguments[0];
    for(var i=1;i<arguments.length;i++) {
    var re = new RegExp('\\{' + (i-1) + '\\}','gm');
    str = str.replace(re, arguments[i]);
    }
    return str;
}


</script>
%rebase admin_frame_base
