(()=>{
 'use strict';
 const $=id=>document.getElementById(id), config=window.SOURCE_CONFIG;
 if(config.offline){
  const section=$('page-sources');
  section.querySelector('.section-head').insertAdjacentHTML('afterend','<div class="card source-panel"><p>当前是 HTML 报告快照。上传、SQL 查询和保存修改请先运行项目根目录的 start.cmd，再打开完整网站。</p><a class="btn btn-primary" href="http://127.0.0.1:8867/#sources">打开可上传和修改的数据源</a></div>');
  section.querySelectorAll('input,textarea,select,button').forEach(e=>e.disabled=true);
  section.querySelectorAll('a[href^="/api/"]').forEach(e=>{e.href='http://127.0.0.1:8867/#sources';});
  $('source-sql-toggle').disabled=false;$('source-sql-toggle').onclick=()=>{$('source-sql-panel').hidden=!$('source-sql-panel').hidden};
  $('source-edit-focus').disabled=false;$('source-edit-focus').onclick=()=>$('source-editor').scrollIntoView({behavior:'smooth'});
  const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  $('source-table').disabled=false;
  function preview(){const key=$('source-table').value,fields=config.fields[key],rows=config.tables[key];
   $('source-editor').innerHTML='<table><thead><tr>'+fields.map(f=>'<th>'+escape(f)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+fields.map(f=>'<td>'+escape(r[f])+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
   $('source-meta').textContent=key+' · '+config.counts[key]+' 行';$('source-page').textContent='快照预览前 '+rows.length+' 行';
  }
  $('source-table').onchange=preview;preview();$('source-message').textContent='完整网站中可上传、映射、编辑、应用更新和撤销。';return;
 }
 const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const labels={line_id:'明细行 ID',order_id:'订单 ID',order_date:'订单时间',customer_id:'客户 ID',product:'产品名称',sku:'SKU 名称',channel:'渠道',quantity:'购买件数',returned_quantity:'退货件数',gmv_cny:'GMV（CNY）',net_sales_cny:'净收入（CNY）',month:'月份',impressions:'曝光',page_views:'浏览',unique_page_views:'去重浏览',unique_customers:'去重客户',target_gmv_cny:'目标 GMV（CNY）'};
 const help={orders:'每行是一条订单商品明细，line_id 唯一；日期示例 2026-04-15T14:00:00；渠道使用 douyin（抖系）/ taobao（淘系）/ jd（京系）。金额是该明细行合计金额，不是单价。',traffic:'每个月 × 产品 × 渠道一行。请提供真实曝光和浏览量；缺少数据时转化图表将提示补充，不会从订单金额推算。',targets:'每月一行，月份格式 YYYY-MM。新增订单月份前，请先补充月度目标。'};
 let saved,table='orders',draft=[],page=0,dirty=false,source='',sheets={},importName='',busy=false;
 function message(text,error=false){$('source-message').textContent=text;$('source-message').dataset.error=String(error)}
 async function api(url,data){const response=await fetch(url,{method:data?'POST':'GET',headers:data instanceof FormData?{'X-Local-Token':config.token}:data?{'Content-Type':'application/json','X-Local-Token':config.token}:{},body:data instanceof FormData?data:data?JSON.stringify(data):undefined});const result=await response.json();if(!response.ok)throw new Error(result.error||'请求失败');return result}
 async function run(fn){if(busy)return;busy=true;const buttons=[...document.querySelectorAll('#page-sources button')];buttons.forEach(b=>b.disabled=true);try{await fn()}catch(e){message(e.message,true)}finally{busy=false;buttons.forEach(b=>b.disabled=false);pagination()}}
 function resetDraft(){draft=structuredClone(saved.tables[table]);page=0;dirty=false;source=saved.sources[table];render();message('数据已载入。编辑后点击“应用到看板”。')}
 function pagination(){if(!saved)return;$('source-prev').disabled=busy||page===0;$('source-next').disabled=busy||(page+1)*30>=draft.length;$('source-page').textContent=`第 ${page+1} / ${Math.max(1,Math.ceil(draft.length/30))} 页 · ${draft.length.toLocaleString()} 行`}
 function render(){
  const fields=config.fields[table];$('source-help').textContent=help[table];$('source-export').href=`/api/export/${table}.csv`;
  $('source-meta').innerHTML=Object.keys(config.fields).map(k=>`<span>${escape(k)}：${escape(saved.sources[k])} · ${saved.tables[k].length} 行</span>`).join('');
  $('source-editor').innerHTML=`<table><thead><tr><th>行</th>${fields.map(f=>`<th>${escape(labels[f])}<br><small>${f}</small></th>`).join('')}<th>操作</th></tr></thead><tbody>${draft.slice(page*30,(page+1)*30).map((row,i)=>`<tr><td>${page*30+i+1}</td>${fields.map(f=>`<td><input aria-label="第 ${page*30+i+1} 行 ${escape(labels[f])}" data-row="${page*30+i}" data-field="${f}" value="${escape(row[f])}"></td>`).join('')}<td><button data-delete="${page*30+i}">删除</button></td></tr>`).join('')}</tbody></table>`;
  pagination();
 }
 $('source-editor').addEventListener('input',e=>{if(e.target.dataset.field){draft[Number(e.target.dataset.row)][e.target.dataset.field]=e.target.value;dirty=true;source='在线编辑';message('有未应用的修改。应用后会重新计算全部图表。')}});
 $('source-editor').addEventListener('click',e=>{if(e.target.dataset.delete!==undefined){draft.splice(Number(e.target.dataset.delete),1);page=Math.min(page,Math.max(0,Math.ceil(draft.length/30)-1));dirty=true;source='在线编辑';render();message('已从草稿删除该行，尚未应用。')}});
 $('source-table').addEventListener('change',()=>{if(dirty&&!confirm('切换数据表会放弃当前未应用的草稿，是否继续？')){$('source-table').value=table;return}table=$('source-table').value;resetDraft();if(Object.keys(sheets).length)mapping()});
 $('source-add').onclick=()=>{draft.push(Object.fromEntries(config.fields[table].map(f=>[f,''])));page=Math.floor((draft.length-1)/30);dirty=true;source='在线编辑';render();message('请填完新增行的全部字段后应用。')};
 $('source-prev').onclick=()=>{page--;render()};$('source-next').onclick=()=>{page++;render()};
 $('source-discard').onclick=()=>{if(!dirty||confirm('放弃当前草稿？'))resetDraft()};
 $('source-save').onclick=()=>run(async()=>{message('正在校验和重算…');await api('/api/apply',{version:saved.version,table,rows:draft,source});dirty=false;location.hash='sources';location.reload()});
 $('source-undo').onclick=()=>run(async()=>{if(confirm('撤销上一次已应用的数据更新？')){await api('/api/restore',{version:saved.version});dirty=false;location.hash='sources';location.reload()}});
 $('source-edit-focus').onclick=()=>$('source-editor').scrollIntoView({behavior:'smooth',block:'center'});
 $('source-sql-toggle').onclick=()=>{$('source-sql-panel').hidden=!$('source-sql-panel').hidden};
 $('sql-path').value=config.demoDatabase;
 $('sql-engine').onchange=()=>{const remote=$('sql-engine').value!=='sqlite';$('sql-remote').hidden=!remote;$('sqlite-path-label').hidden=remote;$('sql-port').value=$('sql-engine').value==='mysql'?'3306':'5432'};
 function openImport(value,name){sheets=value;importName=name;$('source-import-panel').hidden=false;$('source-sheet').innerHTML=Object.keys(sheets).map(k=>`<option value="${escape(k)}">${escape(k)}</option>`).join('');if(sheets[table])$('source-sheet').value=table;mapping();$('source-import-panel').scrollIntoView({behavior:'smooth',block:'start'})}
 function mapping(){const sheet=sheets[$('source-sheet').value];if(!sheet)return;
  $('source-mapping').innerHTML=config.fields[table].map(f=>{const selected=sheet.headers.includes(f)?f:sheet.headers.includes(labels[f])?labels[f]:'';return `<label>${escape(labels[f])} · ${f}<select data-map="${f}" aria-label="映射 ${f}"><option value="">请选择来源列</option>${sheet.headers.map(h=>`<option value="${escape(h)}" ${h===selected?'selected':''}>${escape(h)}</option>`).join('')}</select></label>`}).join('');
  $('source-preview').innerHTML=`<table><thead><tr>${sheet.headers.map(h=>`<th>${escape(h)}</th>`).join('')}</tr></thead><tbody>${sheet.rows.slice(0,5).map(row=>`<tr>${sheet.headers.map(h=>`<td>${escape(row[h])}</td>`).join('')}</tr>`).join('')}</tbody></table><p>共 ${sheet.rows.length} 行，此处显示前 5 行。</p>`;
 }
 $('source-sheet').onchange=mapping;
 $('source-import-cancel').onclick=()=>{$('source-import-panel').hidden=true;sheets={}};
 $('source-file').onchange=()=>run(async()=>{const file=$('source-file').files[0];if(!file)return;message('正在读取文件…');const data=new FormData();data.append('file',file);const result=await api('/api/upload',data);openImport(result.sheets,'文件：'+file.name);message('文件已读取，请检查字段映射。');$('source-file').value=''});
 $('source-map-apply').onclick=()=>{const maps=[...document.querySelectorAll('[data-map]')];if(maps.some(s=>!s.value)){message('每个必需字段都要选择来源列。',true);return}if(dirty&&!confirm('导入将替换当前草稿，继续？'))return;draft=sheets[$('source-sheet').value].rows.map(r=>Object.fromEntries(maps.map(s=>[s.dataset.map,r[s.value]??''])));page=0;dirty=true;source=importName;render();message(`已载入 ${draft.length} 行草稿，请检查后应用到看板。`);$('source-editor').scrollIntoView({behavior:'smooth',block:'center'})};
 $('source-query').onclick=()=>run(async()=>{message('正在建立只读连接并查询…');try{const result=await api('/api/sql',{engine:$('sql-engine').value,path:$('sql-path').value,host:$('sql-host').value,port:$('sql-port').value,database:$('sql-database').value,user:$('sql-user').value,password:$('sql-password').value,query:$('sql-query').value});openImport({'SQL 查询':result},'SQL：'+$('sql-engine').value);message(`SQL 查询成功：${result.rows.length} 行。请映射后载入编辑器。`)}finally{$('sql-password').value=''}});
 window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});
 run(async()=>{saved=await api('/api/state');resetDraft()});
})();
