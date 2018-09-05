%if info['submitUrl'][-6:] == 'create':
<tr>
     <td class='table-title'>
                是否允许试玩<br/>
                <small>设置为试玩则改房间为试玩房间</small>
         </td>
         <td>
              <input type="radio"  name="isTrail" value='0' checked="checked"/> 不允许
              <input type="radio"  name="isTrail" value='1'/> 允许
         </td>
</tr>
<tr>
         <td class='table-title'>
                限制金币<br/>
                <small>是否限制玩家携带的金币</small>
         </td>
         <td>
              最小携带金币:<br>
              <input type="text" style='width:100%;float:left' id="min_coin" name="min_coin" class="form-control" />
              最大携带金币:<br>
              <input type="text" style='width:100%;float:left' id="max_coin" name="max_coin" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                房间最大人数<br/>
                <small>改房间允许的最大玩家人数</small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="max_player_count" name="max_player_count" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                房间抽水<br/>
                <small>按抽比例</small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="tax_rate" name="tax_rate" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                投放鱼的下限<br/>
                <small></small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="min_add" name="min_add" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                投放鱼的上限<br/>
                <small></small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="max_add" name="max_add" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                击中鱼的次数配置<br/>
                <small>
                        打中鱼至少需要的击打次数<br/>
                        格式:{鱼编号1:击打次数,鱼编号2:击打次数 ...}
                </small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="fish_need_count" name="fish_need_count" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                鱼投放配置<br/>
                <small>
                    不添加鱼编号则不限制鱼个数，投放个数为0则不投放<br/>
                    格式:{鱼编号1:投放个数, 鱼编号2:投放个数 ...}
                </small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="fish_limit_count" name="fish_limit_count" class="form-control" />
         </td>
</tr>
%else:
<tr>
     <td class='table-title'>
                是否允许试玩<br/>
                <small>设置为试玩则改房间为试玩房间</small>
         </td>
         <td v-if="roomInfo.isTrail == '0'">
              <input type="radio"  name="isTrail" value='0' checked="checked"/> 不允许
              <input type="radio"  name="isTrail" value='1'/> 允许
         </td>
         <td v-if="roomInfo.isTrail == '1'">
             <input type="radio"  name="isTrail" value='0'/> 不允许
             <input type="radio"  name="isTrail" value='1' checked="checked"/> 允许
         </td>
</tr>
<tr>
         <td class='table-title'>
                限制金币<br/>
                <small>是否限制玩家携带的金币</small>
         </td>
         <td>
              最小携带金币:<br>
              <input type="text" style='width:100%;float:left' v-bind:value="roomInfo.min_coin" id="min_coin" name="min_coin" class="form-control" />
              最大携带金币:<br>
              <input type="text" style='width:100%;float:left' v-bind:value="roomInfo.max_coin" id="max_coin" name="max_coin" class="form-control" />
         </td>
    </tr>
</tr>
<tr>
         <td class='table-title'>
                房间最大人数<br/>
                <small>改房间允许的最大玩家人数</small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left'  v-bind:value="roomInfo.max_player_count" id="max_player_count" name="max_player_count" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                房间难度<br/>
                <small>难度等级</small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="tax_rate" name="tax_rate" v-bind:value="roomInfo.tax_rate" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                投放鱼的下限<br/>
                <small></small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="min_add" name="min_add" :value="roomInfo.min_add" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                投放鱼的上限<br/>
                <small></small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="max_add" name="max_add" :value="roomInfo.max_add" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                击中鱼的次数配置<br/>
                <small>
                        打中鱼至少需要的击打次数<br/>
                        格式:{鱼编号1:击打次数, 鱼编号2:击打次数 ...}
                </small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="fish_need_count" name="fish_need_count" :value="roomInfo.fish_need_count" class="form-control" />
         </td>
</tr>
<tr>
         <td class='table-title'>
                鱼投放配置<br/>
                <small>
                    不添加鱼编号则不限制鱼个数，投放个数为0则不投放<br/>
                    格式:{鱼编号1:投放个数, 鱼编号2:投放个数 ...}
                </small>
         </td>
         <td>
              <input type="text" style='width:100%;float:left' id="fish_limit_count" name="fish_limit_count" :value="roomInfo.fish_limit_count" class="form-control" />
         </td>
</tr>
%end
