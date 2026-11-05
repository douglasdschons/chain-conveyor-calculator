"""Regression tests of the app flows and printed report, no Streamlit required."""
import sys, types, runpy, unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app.py'
class Ctx:
 def __enter__(self): return self
 def __exit__(self,*a): return False
 def container(self): return self
class Fake(types.ModuleType):
 def __init__(self,ret='Retorno guiado',connection='Direto',drive='Motoredutor completo',fs=1.,ratio=40):
  super().__init__('streamlit');self.session_state={'application_service_factor':fs};self.ret=ret;self.connection=connection;self.drive=drive;self.ratio=ratio;self.markup=[];self.downloads=[];self.inputs=[]
 def columns(self,kind,**kw):return [Ctx() for _ in range(kind if isinstance(kind,int) else len(kind))]
 def container(self):return Ctx()
 def empty(self):return Ctx()
 def expander(self,*a,**kw):return Ctx()
 def toggle(self,*a,**kw):return kw.get('value',False)
 def radio(self,label,options,*a,**kw):return {'Tipo de acionamento':self.drive,'Conexão':self.connection}.get(label,options[0])
 def selectbox(self,label,options,*a,**kw):
  if label=='Tipo de retorno':return self.ret
  if label=='Redução i (1:i)':return self.ratio
  key=kw.get('key');v=options[kw.get('index',0)];return self.session_state.setdefault(key,v) if key else v
 def text_input(self,label,value='',*a,**kw):
  self.inputs.append(label);return self.session_state.get(kw.get('key'),value) if kw.get('key') else value
 def markdown(self,html,*a,**kw):self.markup.append(html)
 def download_button(self,label,*,data,file_name,mime,**kw):self.downloads.append((label,data.decode(),file_name,mime))
 def __getattr__(self,name):
  if name in ('set_page_config','title','warning','error','image','caption','stop'):return lambda *a,**kw:None
  raise AttributeError(name)

def invoke(**kw):
 old=sys.modules.get('streamlit');fake=Fake(**kw)
 try:
  sys.modules['streamlit']=fake;env=runpy.run_path(str(APP));return env,fake
 finally:
  if old is None:sys.modules.pop('streamlit',None)
  else:sys.modules['streamlit']=old

class AppSmoke(unittest.TestCase):
 def test_baseline_manual(self):
  e,f=invoke();c=e['conveyor']
  self.assertEqual((e['center_distance_m'],e['conveyor_dp'],e['mu_top'],e['service_factor']),(4.5,202.66,.25,1.))
  for k,v in [('top_chain_mass_kg',131.4),('top_supported_mass_kg',407.4),('total_chain_mass_kg',281.39091488),('top_friction_n',999.1485),('return_friction_n',322.2585),('regime_force_n',1321.407),('acceleration_force_n',108.38156678),('force_before_design_factor_n',1429.78856678),('required_axis_torque_nm',144.88047547),('required_axis_power_kw',.8340433306),('required_axis_speed_rpm',54.97308801)]:
   self.assertAlmostEqual(getattr(c,k),v,places=5,msg=k)
  self.assertAlmostEqual(e['corrected_torque_nm'],144.88047547,places=5)
  self.assertIn('Fator de serviço', ''.join(f.markup))
 def test_fs_not_double_counted(self):
  e1,_=invoke(fs=1.);e2,_=invoke(fs=1.5)
  self.assertAlmostEqual(e2['corrected_torque_nm']/e1['corrected_torque_nm'],1.5)
  self.assertAlmostEqual(e2['corrected_power_kw']/e1['corrected_power_kw'],1.5)
  self.assertAlmostEqual(e2['conveyor'].required_axis_torque_nm,e1['conveyor'].required_axis_torque_nm)
  self.assertAlmostEqual(e2['final_output'].axis_torque_nm,e1['final_output'].axis_torque_nm)
 def test_catalogue_ratio_updates_available(self):
  a,_=invoke(ratio=40);b,_=invoke(ratio=30)
  self.assertAlmostEqual(a['final_output'].axis_speed_rpm,42.5,places=5)
  self.assertAlmostEqual(b['final_output'].axis_speed_rpm,1700/30,places=5)
  self.assertAlmostEqual(a['final_output'].axis_torque_nm,366.8,places=5)
  self.assertAlmostEqual(b['final_output'].axis_torque_nm,396.5*3/4,places=5)
  self.assertNotEqual(a['compare_rows'][0],b['compare_rows'][0]);self.assertNotEqual(a['compare_rows'][2],b['compare_rows'][2]);self.assertNotEqual(a['compare_rows'][3],b['compare_rows'][3])
 def test_eight_ui_branches(self):
  for ret in ('Retorno guiado','Retorno livre com flecha'):
   for conn in ('Direto','Transmissão secundária por corrente'):
    for drv in ('Motoredutor completo','Redutor e motor separados'):
     with self.subTest(ret=ret,conn=conn,drv=drv):
      e,f=invoke(ret=ret,connection=conn,drive=drv)
      self.assertEqual(len(e['compare_rows'][0]),6)
      self.assertEqual(len(f.downloads),1)
      self.assertIn('CAPACIDADE DISPONÍVEL', ''.join(f.markup))
 def test_html_report_and_escape(self):
  e,f=invoke();lab,html,name,mime=f.downloads[0]
  self.assertEqual(mime,'text/html');self.assertIn('window.print()',html)
  self.assertIn('Fator de serviço da aplicação',html)
  self.assertIn('144,88',html);self.assertIn('1.429,79',html)
  self.assertTrue(name.endswith('.html'))
  rendered=e['build_print_report']([('a',[('b','<script>')])],[('x','y','z','r','m','ok')],['A & B'])
  self.assertIn('&lt;script&gt;',rendered);self.assertNotIn('<script>',rendered)
if __name__=='__main__':unittest.main()
