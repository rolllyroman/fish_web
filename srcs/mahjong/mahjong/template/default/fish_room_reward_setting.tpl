%if info['submitUrl'][-6:] == 'create':
<tr>
     <td class='table-title'>
                基本金币<br/>
                <small></small>
         </td>
         <td>
              <input type="text"  style='width:100%;float:left' class="form-control" name="need_coin" value='' checked="checked"/>
         </td>
</tr>
<tr>
         <td class='table-title'>
                金币价值<br/>
                <small></small>
         </td>
         <td>
            <input type="text"   style='width:100%;float:left' class="form-control" name="coin_value" value='' checked="checked"/>
         </td>
</tr>
<tr>
         <td class='table-title'>
                奖票产出百分比<br/>
                <small></small>
         </td>
         <td>
            <input type="text"   style='width:100%;float:left' class="form-control" name="get_rate" value='' checked="checked"/>
         </td>
</tr>
<tr>
         <td class='table-title'>
                单次获得最大张数<br/>
                <small></small>
         </td>
         <td>
            <input type="text"   style='width:100%;float:left' class="form-control" name="max_ticket_count" value='' checked="checked"/>
         </td>
</tr>
<tr>
         <td class='table-title'>
                获得奖票间隔时间<br/>
                <small>
                        格式:[间隔时间1,间隔时间2,...]
                </small>
         </td>
         <td>
            <input type="text"   style='width:100%;float:left' class="form-control" name="ticket_wait_time" value='' checked="checked"/>
         </td>
</tr>

%else:
<tr>
     <td class='table-title'>
                基本金币<br/>
                <small></small>
         </td>
         <td>
              <input type="text"  style='width:100%;float:left' class="form-control" name="need_coin" v-bind:value="roomInfo.need_coin" checked="checked"/>
         </td>
</tr>
<tr>
         <td class='table-title'>
                金币价值<br/>
                <small></small>
         </td>
         <td>
            <input type="text" style='width:100%;float:left'  class="form-control" name="coin_value" v-bind:value="roomInfo.coin_value" >
         </td>
</tr>
<tr>
         <td class='table-title'>
                奖票产出百分比<br/>
                <small></small>
         </td>
         <td>
            <input type="text" style='width:100%;float:left'  class="form-control" name="get_rate" :value="roomInfo.get_rate" >
         </td>
</tr>
<tr>
         <td class='table-title'>
                单次获得最大张数<br/>
                <small></small>
         </td>
         <td>
            <input type="text"   style='width:100%;float:left' class="form-control" name="max_ticket_count" :value='roomInfo.max_ticket_count' checked="checked"/>
         </td>
</tr>
<tr>
         <td class='table-title'>
                获得奖票间隔时间<br/>
                <small>
                        格式:[间隔时间1,间隔时间2,...]
                </small>
         </td>
         <td>
            <input type="text"   style='width:100%;float:left' class="form-control" name="ticket_wait_time" :value='roomInfo.ticket_wait_time' checked="checked"/>
         </td>
</tr>
%end
