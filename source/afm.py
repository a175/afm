#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import string, time
import pango
import cairo
import poppler
import sys
import zipfile
import os.path
import os
import urllib
import urlparse

def get_int_from_spinbutton(spinbutton):
  if spinbutton.get_text():
    return int(spinbutton.get_text())
  else:
    return spinbutton.get_value_as_int()


def int2alphabet(n):
  r=""
  while n>19:
    r=chr(ord('A')+(n%20))+r
    n=(n-(n%20))//20
  return  chr(ord('A')+n)+r

#####################################################
class applicationFormData:

  def create_bgimage_file(self,pdffullpath,destzip,rootdir):    
    destzip.write(pdffullpath,os.path.join(rootdir,self.pdffilename()))

  def __init__(self,listOfBoxData,pdf_filename,boundingboxes):
    self.UNITLENGTH=1.0
    self.XMARGIN=1.0
    self.YMARGIN=1.0

    self.PREFIX_ENVAT=""
    self.SUFFIX_ENVAT="@env@nu"
    self.PREFIX_COMAT=""
    self.SUFFIX_COMAT="@com@nu"
    self.PREFIX_BASEAT=""
    self.SUFFIX_BASEAT="@@nu"    
    self.PREFIX_ROUNDRECTANGLEAT=""
    self.SUFFIX_ROUNDRECTANGLEAT="@roundrectangle@nu"

    self.bgfilename=pdf_filename
    n_page=0
    for boxdata in listOfBoxData:
      if n_page < boxdata.page+1:
        n_page=boxdata.page+1

    self.boundingboxes=[]
    page=[]
    for i in range(n_page):
      (ltx,lty,rbx,rby)=boundingboxes[i]
      self.boundingboxes.append((int(ltx),int(lty),int(rbx),int(rby)))
      p=[]
      page.append(p)
      for boxdata in listOfBoxData:
        if boxdata.page==i:
          p.append(boxdata)
    self.page=page

  def get_boundingboxstring(self,n):
    (ltx,lty,rbx,rby)=self.boundingboxes[n]
    r=str(ltx)+' '+str(lty)+' '+str(rbx)+' '+str(rby)
    return r

  def dtppt2texpt(self,dtp_pt):
    return dtp_pt*(72.27)/(72.0)
  def dtppt2unitlength(self,dtp_pt):
    return self.dtppt2texpt(dtp_pt)/self.UNITLENGTH
  def dtppt2unitlength_as_str(self,dtp_pt):
    return str(self.dtppt2unitlength(dtp_pt))
  def envATname(self,name):
    return self.PREFIX_ENVAT+name+self.SUFFIX_ENVAT
  def comATname(self,name):
    return "\\"+self.PREFIX_COMAT+name+self.SUFFIX_COMAT
  def baseATname(self,name):
    return "\\"+self.PREFIX_BASEAT+name+self.SUFFIX_BASEAT    
  def roundrectangleATname(self,name):
    return "\\"+self.PREFIX_BASEAT+name+self.SUFFIX_ROUNDRECTANGLEAT    
  def env_minipage(self,boxdata):
    width=self.dtppt2unitlength_as_str(boxdata.width)
    begin_minipage=r'\begin{minipage}[c]{'+width+r'\unitlength}'
    end_minipage=r'\end{minipage}'
    if boxdata.halign==BoxData.HALIGN_RIGHT:
      begin_minipage=begin_minipage+r'\begin{flushright}'      
      end_minipage=r'\end{flushright}'+end_minipage      
    elif boxdata.halign==BoxData.HALIGN_CENTER:
      begin_minipage=begin_minipage+r'\begin{center}'      
      end_minipage=r'\end{center}'+end_minipage      
    return (begin_minipage,end_minipage)    
  def com_makebox(self,boxdata):
    r=r'\makebox(0,0)'
    if boxdata.valign==BoxData.VALIGN_BOTTOM:
      r=r+'[bl]'
    elif boxdata.valign==BoxData.VALIGN_TOP:
      r=r+'[tl]'
    else:
      r=r+'[l]'
    return r
  def form_sample(self,boxdata):
    r=""
    if boxdata.type==BoxData.TYPE_ENVIRONMENT:
      r=r +r'\begin{'
      r=r + boxdata.name
      r=r +r'}'
      r=r +'\n'
      r=r + boxdata.sampletext
      r=r +'\n'
      r=r +r'\end{'
      r=r + boxdata.name
      r=r +r'}'
    elif boxdata.type==BoxData.TYPE_COMMAND:
      r=r +'\\'
      r=r + boxdata.name
      r=r +'{'
      r=r + boxdata.sampletext
      r=r +'}'
    elif boxdata.type==BoxData.TYPE_CHECKMARK:
      r=r +'\\'
      r=r + boxdata.name
    elif boxdata.type!=BoxData.TYPE_STRIKE:
      r=r +'\\'
      r=r + boxdata.name
    elif boxdata.type!=BoxData.TYPE_RULE:
      r=r +'\\'
      r=r + boxdata.name
    return r
  def formfrontenddef(self,boxdata):
    r=""
    if boxdata.type!=BoxData.TYPE_ENVIRONMENT:
      r=r+"% "
    r=r +r'\newenvironment{'
    r=r + boxdata.name
    r=r +r'}{\begin{'
    r=r + self.envATname(boxdata.name)
    r=r +r'}}{\end{'
    r=r + self.envATname(boxdata.name)
    r=r +r'}}'

    if boxdata.type!=BoxData.TYPE_COMMAND:
      r=r+"\n% "
    else:
      r=r+"\n"
    r=r +r'\newcommand{'+"\\"
    r=r + boxdata.name
    r=r +r'}{'
    r=r + self.comATname(boxdata.name)
    r=r +r'}'

    if boxdata.type!=BoxData.TYPE_CHECKMARK:
      r=r+"\n% "
    else:
      r=r+"\n"
    r=r +r'\newcommand{'+"\\"
    r=r + boxdata.name
    r=r +r'}{'
    r=r + self.comATname(boxdata.name)
    r=r +r'{$\checkmark$}}'

    if boxdata.type!=BoxData.TYPE_STRIKE:
      r=r+"\n% "
    else:
      r=r+"\n"
    r=r +r'\newcommand{'+"\\"
    r=r + boxdata.name
    r=r +r'}{'
    r=r + self.comATname(boxdata.name)
    r=r +r'{\rule{'
    r=r + self.dtppt2unitlength_as_str(boxdata.width)
    r=r +r'\unitlength}{'
    r=r + self.dtppt2unitlength_as_str(boxdata.height/6)
    r=r +r'\unitlength}\kern -'
    r=r + self.dtppt2unitlength_as_str(boxdata.width)
    r=r +r'\unitlength\rule['
    r=r + self.dtppt2unitlength_as_str(5*boxdata.height/6)
    r=r +r'\unitlength]{'
    r=r + self.dtppt2unitlength_as_str(boxdata.width)
    r=r +r'\unitlength}{'
    r=r + self.dtppt2unitlength_as_str(boxdata.height/6)
    r=r +r'\unitlength}}'
    r=r +r'}'


    if boxdata.type!=BoxData.TYPE_RULE:
      r=r+"\n% "
    else:
      r=r+"\n"
    r=r +r'\newcommand{'+"\\"
    r=r + boxdata.name
    r=r +r'}{'
    r=r + self.comATname(boxdata.name)
    r=r +r'{\rule{'
    r=r + self.dtppt2unitlength_as_str(boxdata.width)
    r=r +r'\unitlength}{'
    r=r + self.dtppt2unitlength_as_str(boxdata.height)
    r=r +r'\unitlength}}}'


    if boxdata.type!=BoxData.TYPE_CHECK_CIRCLE:
      r=r+"\n% "
    else:
      r=r+"\n"
    r=r +r'\newcommand{'+"\\"
    r=r + boxdata.name
    r=r +r'}{'
    r=r + self.roundrectangleATname(boxdata.name)
    r=r +r'}'
  
    return r



  def formdef(self,boxdata):
    x=self.dtppt2unitlength_as_str(boxdata.x-self.XMARGIN)
    if boxdata.valign==BoxData.VALIGN_BOTTOM:
      y=-boxdata.y-boxdata.height
    elif boxdata.valign==BoxData.VALIGN_CENTER:
      y=-boxdata.y-0.5*boxdata.height
    else:
      y=-boxdata.y
    y=self.dtppt2unitlength_as_str(y+self.YMARGIN)


    (begin_minipage,end_minipage)=self.env_minipage(boxdata)
    com_makebox=self.com_makebox(boxdata)
    env_at=self.envATname(boxdata.name)
    com_at=self.comATname(boxdata.name)
    base_at=self.baseATname(boxdata.name)

    r=""
    r=r +r'\newenvironment{'
    r=r + env_at
    r=r +r'}{\begin{lrbox}{\MyBlackBox@nu}'
    r=r + begin_minipage
    r=r +r'}{'
    r=r + end_minipage
    r=r +r'\end{lrbox}'
    r=r + base_at
    r=r +r'{\usebox{\MyBlackBox@nu}}}'
    new_env_at=r

    r=""
    r=r +r'\newcommand{'
    r=r + com_at
    r=r +r'}[1]{'
    r=r + base_at
    r=r +r'{'
    r=r +begin_minipage+'#1'+end_minipage+'}}'
    new_com_at=r

    r=""
    r=r +r'\newcommand{'
    r=r + base_at
    r=r +r'}[1]{\put('
    r=r + x
    r=r +r','
    r=r + y
    r=r +r'){'
    r=r + com_makebox
    r=r +r'{{#1}}}}'
    new_base_at=r



    put_roundrectangle_at=self.roundrectangleATname(boxdata.name)
    midx=self.dtppt2unitlength_as_str(boxdata.x+0.5*boxdata.width-self.XMARGIN)
    midy=self.dtppt2unitlength_as_str(-boxdata.y-0.5*boxdata.height+self.YMARGIN)
    round_R=min(boxdata.width,boxdata.height)
    if round_R >20:
      round_R=20
    round_r=int(0.5*round_R)
    round_wr=int(0.5*boxdata.width)
    round_hr=int(0.5*boxdata.height)
    round_w=round_wr-round_r
    round_h=round_hr-round_r

    r=""
    r=r +r'\newcommand{'
    r=r + put_roundrectangle_at
    r=r +r'}{\put('
    r=r + midx
    r=r +r','
    r=r + midy
    r=r +r'){'
    if round_R <5:
      r=r +r'\makebox(0,0)[c]{$\circ$}'
    else:
      r=r +r'\roundCorners@nu['
      r=r + self.dtppt2unitlength_as_str(round_r*2)

      r=r +r']{'
      r=r + self.dtppt2unitlength_as_str(round_w)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_h)
      r=r +r'}'
      r=r +r'\boxWithoutCorners@nu{'
      r=r + self.dtppt2unitlength_as_str(round_w)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_h)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_wr)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_hr)
      r=r +r'}'
    r=r +r'}}'
    new_roundrectangle_at=r


    return (new_env_at,new_com_at,new_base_at,new_roundrectangle_at)


  def page_atfirst(self,n):
    return r'\pageNo'+int2alphabet(n)+r'AtFirst'
  def def_page_atfirst(self,n):
    return r'\newcommand{'+self.page_atfirst(n)+r'}{}'
  def pagename_frontend(self,n):
    return "pageNo"+int2alphabet(n)
  def pagename_none(self,n):
    return self.pagename_frontend(n)+"*"
  def pagename_pdf(self,n):
    return self.pagename_frontend(n)+"**"
  def pdffilename(self):
    return self.bgfilename
  def pagedef(self,n):
    r=""
    r=r +r'\newenvironment{'
    r=r + self.pagename_pdf(n)
    r=r +r'}{\thispagestyle{empty}\begin{overwrappicture}[bb='
    r=r + self.get_boundingboxstring(n)
    r=r +r', page='
    r=r +str(n+1)
    r=r +r']{'
    r=r + self.pdffilename()
    r=r +r'}'
    r=r + self.page_atfirst(n)
    r=r +r'}{\end{overwrappicture}}'
    pdf=r

    r=""
    r=r +r'\newenvironment{'
    r=r + self.pagename_none(n)
    r=r +r'}{\thispagestyle{empty}\begin{overwrappicture*}[bb='
    r=r + self.get_boundingboxstring(n)
    r=r +r', page='
    r=r +str(n+1)
    r=r +r']{'
    r=r + self.pdffilename()
    r=r +r'}'
    r=r + self.page_atfirst(n)
    r=r +r'}{\end{overwrappicture*}}'
    no=r
    
    r=''
    r=r +r"\if@PDF@image@type@nu@"
    r=r +r'\newenvironment{'
    r=r + self.pagename_frontend(n)
    r=r +r'}{\begin{'
    r=r + self.pagename_pdf(n)
    r=r +r'}}{\end{'
    r=r + self.pagename_pdf(n)
    r=r +r'}}'  +"\n"
    r=r +r'\else' +"\n"
    r=r +r'\newenvironment{'
    r=r + self.pagename_frontend(n)
    r=r +r'}{\begin{'
    r=r + self.pagename_none(n)
    r=r +r'}}{\end{'
    r=r + self.pagename_none(n)
    r=r +r'}}'+"\n"
    r=r +r'\fi'
    fr=r
    return (fr,no,pdf)

  def common_command(self):
    return r'''
\NeedsTeXFormat{LaTeX2e}
\RequirePackage{geometry}
\geometry{ignoreall,scale=1}

\newif\if@PDF@image@type@nu@
\@PDF@image@type@nu@true
\newif\if@js@basecls@nu@
\@js@basecls@nu@false

\DeclareOption{pdf}{\@PDF@image@type@nu@true}
\DeclareOption{none}{\@PDF@image@type@nu@false}
\DeclareOption{js}{\@js@basecls@nu@true}
\ProcessOptions\relax

\if@js@basecls@nu@ 
\newcommand{\unitlength@nu}{'''+str(self.UNITLENGTH)+r'''turept}
\else 
\newcommand{\unitlength@nu}{'''+str(self.UNITLENGTH)+r'''pt}
\fi

\newcommand{\baseuplength}{-10}

\newenvironment{overwrappicture}[2][]%
{\newpage\noindent%
\setlength\unitlength\unitlength@nu\begin{picture}(0,0)(0,\baseuplength)%
\put(0,0){\makebox(0,0)[tl]{\includegraphics[#1]{#2}}}}
{\end{picture}}

\newenvironment{overwrappicture*}[2][1]%
{\newpage\noindent%
\setlength\unitlength\unitlength@nu\begin{picture}(0,0)(0,\baseuplength)%
\put(0,0){\makebox(0,0)[tl]{}}}
{\end{picture}}
\newbox{\MyBlackBox@nu}

\newcommand{\roundCorners@nu}[3][20]{\put(#2,#3){\oval(#1,#1)[tr]}\put(-#2,#3){\oval(#1,#1)[tl]}\put(#2,-#3){\oval(#1,#1)[br]}\put(-#2,-#3){\oval(#1,#1)[bl]}}
\newcommand{\boxWithoutCorners@nu}[4]{\put(0,#4){\line(1,0){#1}}\put(0,#4){\line(-1,0){#1}}\put(0,-#4){\line(1,0){#1}}\put(0,-#4){\line(-1,0){#1}}\put(#3,0){\line(0,1){#2}}\put(#3,0){\line(0,-1){#2}}\put(-#3,0){\line(0,1){#2}}\put(-#3,0){\line(0,-1){#2}}}
'''

  def get_style_code(self):
    r="%\n"
    r=r+self.common_command()
    r=r+"%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

    page_atfirst=""
    page_def=""
    form_front=""
    form_back=""

    for i,pagei in enumerate(self.page):
      (fr,no,pdf)=self.pagedef(i)
      page_def=page_def+"\n"+fr+"\n"+no+"\n"+pdf+"\n\n"
      page_atfirst=page_atfirst+"\n"+self.def_page_atfirst(i)
      form_front=form_front+"\n% page "+str(i+1)+" i.e.," +int2alphabet(i)
      for boxdata in pagei:
        form_back=form_back+"\n\n"+("\n".join(self.formdef(boxdata)))
        form_front=form_front+"\n\n"+self.formfrontenddef(boxdata)
    r=r+"%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+page_atfirst
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+form_front
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+page_def
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+form_back
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    return r


  def get_sample_makefile(self,sample_file):
    r="LATEX=latex\nDVI2PDF=dvipdfmx\n"
    r=r+"TEXFILE="+sample_file+"\n\n"
    r=r+"all: pdf\ndvi: ${TEXFILE}.dvi\npdf: ${TEXFILE}.pdf\n\n"
    r=r+"${TEXFILE}.dvi: ${TEXFILE}.tex\n\t${LATEX} ${TEXFILE} && ${LATEX} ${TEXFILE}\n"
    r=r+"${TEXFILE}.pdf: ${TEXFILE}.dvi\n\t${DVI2PDF} ${TEXFILE}.dvi\n"
    r=r+"clean:\n\trm -f ${TEXFILE}.dvi ${TEXFILE}.pdf ${TEXFILE}.log ${TEXFILE}.aux texput.log"
    return r

  def get_sample_code(self,sty_file):
    r=r'''%sample
\documentclass[a4paper,12pt]{amsart}
\nofiles

%\usepackage{graphicx}
%\usepackage[none]{'''+sty_file+r'''}

\usepackage[dvipdfmx]{graphicx}
\usepackage[pdf]{'''+sty_file+r'''}

% If you use the class jsarticle, then use js option
%\usepackage[pdf,js]{'''+sty_file+r'''}

\begin{document}
'''

    for i,pagei in enumerate(self.page):
      r=r+"\n% page"+str(i+1)+"\n"
      r=r+r'\begin{'
      r=r+self.pagename_frontend(i)
      r=r+r'}'
      r=r+"\n"
      for boxdata in pagei:
        r=r+"\n"+self.form_sample(boxdata)
      r=r+"\n"+r'\end{'
      r=r+self.pagename_frontend(i)
      r=r+r'}'
      r=r+"\n\n"
    r=r+r'\end{document}'
    return r


#####################################################

class GridData:
  serialnum=0
  def __init__(self,page,value,is_horizontal,id=None):
    if id==None:
      self.id=GridData.serialnum
      GridData.serialnum=GridData.serialnum+1
    else:
      self.id=id
      GridData.serialnum=max(GridData.serialnum,id)+1
    self.page=page
    self.value=value
    self.is_horizontal=is_horizontal

  
class BoxData:
  serialnum=0
  VALIGN_TOP=1
  VALIGN_BOTTOM=2
  VALIGN_CENTER=3
  DESCRIPTION_VALIGN={1:"top",3:"center",2:"bottom"}

  HALIGN_LEFT=1
  HALIGN_RIGHT=2
  HALIGN_CENTER=3
  DESCRIPTION_HALIGN={1:"left",3:"center",2:"right"}

  TYPE_ENVIRONMENT=0
  TYPE_COMMAND=1
  TYPE_CHECKMARK=2
  TYPE_STRIKE=3
  TYPE_RULE=4
  TYPE_CHECK_CIRCLE=5
  DESCRIPTION_TYPE={0:"environment",1:"command",2:"checkmark",3:"strike",4:"rule",5:"check by circle (or oval)"}

  def int2alphabet(self,n):
    r=""
    while n>19:
      r=chr(ord('A')+(n%20))+r
      n=(n-(n%20))//20
    return  chr(ord('A')+n)+r

  def get_similar_boxdata(self):
    bd=BoxData(self.page,self.x,self.y,self.width,self.height)
    bd.valign=self.valign
    bd.halign=self.halign
    bd.type=self.type
    return bd

  def __init__(self,page,x1,x2,y1,y2):
    self.id=self.int2alphabet(BoxData.serialnum)
    BoxData.serialnum=BoxData.serialnum+1

    self.x_1=x1
    self.x_2=x2
    self.y_1=y1
    self.y_2=y2
    self.name="boxID"+self.id
    self.sampletext="Example of "+self.name
    self.hilight=False
    self.page=page
    self.valign=1
    self.halign=1
    self.type=0



class BoxDataEntryArea:
  COMBO_VALIGN=[("top",BoxData.VALIGN_TOP),("center",BoxData.VALIGN_CENTER),("bottom",BoxData.VALIGN_BOTTOM)]
  COMBO_HALIGN=[("left",BoxData.HALIGN_LEFT),("center",BoxData.HALIGN_CENTER),("right",BoxData.HALIGN_RIGHT)]
  COMBO_TYPE=[("environment",BoxData.TYPE_ENVIRONMENT),("command",BoxData.TYPE_COMMAND),("checkmark",BoxData.TYPE_CHECKMARK),("strike",BoxData.TYPE_STRIKE),("rule",BoxData.TYPE_RULE),("check by circle",BoxData.TYPE_CHECK_CIRCLE)]

  def __init__(self,boxdata,message,projectdata):
    self.projectdata=projectdata
    self.boxdata=boxdata
    vbox=gtk.VBox()
    self.vbox=vbox
    label=gtk.Label()
    label.set_markup(message)
    vbox.pack_start(label,False,False,10)
    table=gtk.Table(2,12)
    vbox.add(table)

    label=gtk.Label()
    label.set_markup("Id")
    table.attach(label,1,2,1,2)
    entry=gtk.Entry()
    table.attach(entry,2,3,1,2)
    entry.set_text(str(boxdata.id))
    entry.set_editable(False)

    label=gtk.Label()
    label.set_markup("Name")
    table.attach(label,1,2,2,3)
    entry=gtk.Entry()
    self.entry_name=entry
    entry.set_text(str(boxdata.name))
    table.attach(entry,2,3,2,3)

    label=gtk.Label()
    label.set_markup("sample text")
    table.attach(label,1,2,3,4)
    entry=gtk.TextView()
    self.entry_sampletext=entry
    entry.get_buffer().set_text(str(boxdata.sampletext))
    self.entry_sampletext=entry
    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    sw.add(entry) 
#    table.attach(entry,2,3,3,4)
    table.attach(sw,2,3,3,4)

    label=gtk.Label()
    label.set_markup("virtical align")
    table.attach(label,1,2,4,5)
#    entry=gtk.Entry()
    combobox = gtk.combo_box_new_text()
    for i,(text,v) in enumerate(self.COMBO_VALIGN):
      combobox.append_text(text)
      if boxdata.valign==v:
        combobox.set_active(i)
    self.entry_valign=combobox
    table.attach(combobox,2,3,4,5)

    label=gtk.Label()
    label.set_markup("horizontal align")
    table.attach(label,1,2,5,6)
    combobox = gtk.combo_box_new_text()
    for i,(text,v) in enumerate(self.COMBO_HALIGN):
      combobox.append_text(text)
      if boxdata.halign==v:
        combobox.set_active(i)
    self.entry_halign=combobox
    table.attach(combobox,2,3,5,6)

    label=gtk.Label()
    label.set_markup("type")
    table.attach(label,1,2,6,7)
    combobox = gtk.combo_box_new_text()
    for i,(text,v) in enumerate(self.COMBO_TYPE):
      combobox.append_text(text)
      if boxdata.type==v:
        combobox.set_active(i)
    self.entry_type=combobox
    table.attach(combobox,2,3,6,7)

    label=gtk.Label()
    label.set_markup("page")
    table.attach(label,1,2,7,8)
    adjustment = gtk.Adjustment(value=boxdata.page,lower=0,upper=projectdata.n_pages,step_incr=1)
    entry=gtk.SpinButton(adjustment)
    self.entry_page=entry
    table.attach(entry,2,3,7,8)

    label=gtk.Label()
    label.set_markup("left")
    table.attach(label,1,2,8,9)
    adjustment = gtk.Adjustment(value=boxdata.x_1,lower=0,upper=projectdata.lwidth,step_incr=1,page_incr=1)

    entry=gtk.SpinButton(adjustment)
    self.entry_x1=entry
    table.attach(entry,2,3,8,9)

    label=gtk.Label()
    label.set_markup("right")
    table.attach(label,1,2,9,10)
    adjustment = gtk.Adjustment(value=boxdata.x_2,lower=0,upper=projectdata.lwidth,step_incr=1,page_incr=1)
    entry=gtk.SpinButton(adjustment)
    self.entry_x2=entry
    table.attach(entry,2,3,9,10)

    label=gtk.Label()
    label.set_markup("top")
    table.attach(label,1,2,10,11)
    adjustment = gtk.Adjustment(value=boxdata.y_1,lower=0,upper=projectdata.lheight,step_incr=1,page_incr=1)
    entry=gtk.SpinButton(adjustment)
    self.entry_y1=entry
    table.attach(entry,2,3,10,11)

    label=gtk.Label()
    label.set_markup("bottom")
    table.attach(label,1,2,11,12)
    adjustment = gtk.Adjustment(value=boxdata.y_2,lower=0,upper=projectdata.lheight,step_incr=1,page_incr=1)
    entry=gtk.SpinButton(adjustment)
    self.entry_y2=entry
    table.attach(entry,2,3,11,12)


#    hbox = gtk.HButtonBox() 
#    table.attach(hbox,2,3,12,13)
#    hbox.set_layout(gtk.BUTTONBOX_END)
#    button = gtk.Button(stock=gtk.STOCK_EDIT)
#    hbox.add(button)
#    self.button_edit=button
#    button.connect('clicked', self.on_click_edit_coordinates)

    self.set_editable_all(True)

    vbox.show_all()

#  def on_click_edit_coordinates(self,widget):
#    (xx,yy,p)=self.get_coordinates()
#    xx=[xx[0],xx[0]+xx[1]]
#    yy=[yy[0],yy[0]+yy[1]]
#    dialog = RulerDialog("select coordinate",None,
#                        gtk.DIALOG_MODAL,
#                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
#                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
#                         self.projectdata,
#                         [True,False],[True,False],xx,yy,p)
    
#    r = dialog.run()
#    self.projectdata.set_default_dialog_size(dialog.get_size())

#    if r==gtk.RESPONSE_ACCEPT:
#      self.set_coordinates(dialog.get_coordinates())
#    dialog.destroy()
#  def set_coordinates(self,coord):
#    xx,yy,p=coord
#    xx.sort()
#    yy.sort()
#    self.entry_page.set_value(p)
#    self.entry_x.set_value(xx[0])
#    self.entry_y.set_value(yy[0])
#    self.entry_width.set_value(xx[1]-xx[0])
#    self.entry_height.set_value(yy[1]-yy[0])
#  def get_coordinates(self):
#    p=self.entry_page.get_value_as_int()
#    x1=self.entry_x.get_value_as_int()
#    y1=self.entry_y.get_value_as_int()
#    x2=self.entry_width.get_value_as_int()
#    y2=self.entry_height.get_value_as_int()
#    return ([x1,x2],[y1,y2],p)
  def get_box(self):
    return self.vbox

  def set_editable_all(self,is_editable):
    self.entry_name.set_editable(is_editable)
    self.entry_sampletext.set_editable(is_editable)
#    self.entry_valign.set_editable(is_editable)
#    self.entry_halign.set_editable(is_editable)
#    self.entry_type.set_editable(is_editable)
    self.entry_page.set_editable(is_editable)
    self.entry_x1.set_editable(is_editable)
    self.entry_x2.set_editable(is_editable)
    self.entry_y1.set_editable(is_editable)
    self.entry_y2.set_editable(is_editable)


  def update_and_get_boxdata(self):
    self.boxdata.name=self.entry_name.get_text()
    (st, end) = self.entry_sampletext.get_buffer().get_bounds()
    self.boxdata.sampletext=self.entry_sampletext.get_buffer().get_text(st,end)
    self.boxdata.valign=self.COMBO_VALIGN[self.entry_valign.get_active()][1]
    self.boxdata.halign=self.COMBO_HALIGN[self.entry_halign.get_active()][1]
    self.boxdata.type=self.COMBO_TYPE[self.entry_type.get_active()][1]
    self.boxdata.hilight=False

    self.boxdata.page=get_int_from_spinbutton(self.entry_page)
    self.boxdata.x1=str(get_int_from_spinbutton(self.entry_x1))
    self.boxdata.x2=str(get_int_from_spinbutton(self.entry_x2))
    self.boxdata.y1=str(get_int_from_spinbutton(self.entry_y1))
    self.boxdata.y2=str(get_int_from_spinbutton(self.entry_y2))

    return self.boxdata


class BoxDataListArea:
  def __init__(self,parent):
    self.parent=parent

    vbox=gtk.VBox()
    self.vbox=vbox

    store = gtk.ListStore (str,str,str, int, int,int,int,int, str,str,str)
    treeview=gtk.TreeView(store)
    self.treeview=treeview
    
    treeview.set_rules_hint(True)
    treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    
    
    tvcolumn = gtk.TreeViewColumn('page')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 3)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn('id')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 0)
    
    tvcolumn = gtk.TreeViewColumn('Neme')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 1)
    
    tvcolumn = gtk.TreeViewColumn('x')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 4)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn('y')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 5)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn('width')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 6)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn('height')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 7)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn('valign')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 8)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn('halign')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 9)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn('type')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 10)
    treeview.set_reorderable(True)



    tvcolumn = gtk.TreeViewColumn('Sample Text')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 2)
    treeview.set_reorderable(True)
    


    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    sw.add(treeview) 
    vbox.add(sw)


    hbox = gtk.HButtonBox() 
    vbox.pack_start(hbox,expand=False, fill=False)
    hbox.set_layout(gtk.BUTTONBOX_END)

    button = gtk.Button(stock=gtk.STOCK_NEW)
    hbox.add(button)
    self.button_new=button
#    button.connect('clicked', self.on_click_add)
    button = gtk.Button(stock=gtk.STOCK_REMOVE)
    hbox.add(button)
    self.button_remove=button
#    button.connect('clicked', self.remove_selected)
    button = gtk.Button(stock=gtk.STOCK_EDIT)
    hbox.add(button)
    self.button_edit=button
#    button.connect('clicked', self.edit_selected)

    button = gtk.Button(stock=gtk.STOCK_COPY)
    hbox.add(button)
    self.button_copy=button
#    button.connect('clicked', self.edit_selected)

    button = gtk.Button(stock=gtk.STOCK_PASTE)
    hbox.add(button)
    self.button_paste=button
#    button.connect('clicked', self.edit_selected)

    vbox.show_all()
    
  def get_vbox(self):
    return self.vbox

  def get_buttons(self):
    return (self.button_new,self.button_remove,self.button_edit,self.button_copy,self.button_paste)

  def append_boxdata(self,boxdata):
    data=(boxdata.id,boxdata.name,boxdata.sampletext,boxdata.page,boxdata.x_1,boxdata.x_2,boxdata.y_1,boxdata.y_2,BoxData.DESCRIPTION_VALIGN[boxdata.valign],BoxData.DESCRIPTION_HALIGN[boxdata.halign],BoxData.DESCRIPTION_TYPE[boxdata.type])
    self.treeview.get_model().append(data)
  def get_selected_id(self):
    (model,iteralist,idlist)=self.get_selected_ids()
    if iteralist:
      return (model,iteralist[0],idlist[0])
    else:
      return (model,None,None)
  def get_selected_ids(self):
    (model, pathlist) = self.treeview.get_selection().get_selected_rows()
    if pathlist:
      iteralist=[model.get_iter(path)for path in pathlist]
      return (model,iteralist,[model.get(itera,0)[0] for itera in iteralist])
    else:
      return (model,None,None)

class LayoutOverBoxes(gtk.Layout):
  def __init__(self,projectdata):
    gtk.Layout.__init__(self)
    self.message='test text'
    self.width = self.height = 0
    self.connect('size-allocate', self.on_self_size_allocate)
    self.connect('expose-event', self.on_self_expose_event)
    self.projectdata=projectdata
    self.page=0
    if self.projectdata:
      self.back_ground_image = self.projectdata.get_page(self.page)
    else:
      self.back_ground_image = None

  def refresh_preview(self):
    if self.window:
      self.window.invalidate_rect(self.allocation,True) 

  def set_page(self,page):
    if self.projectdata.n_pages>0:
      self.page=page % self.projectdata.n_pages
    else:
      self.page=page
    if self.projectdata:
      self.back_ground_image = self.projectdata.get_page(self.page)

    if self.window:
      self.window.invalidate_rect(self.allocation,True) 

  def on_self_size_allocate(self, widget, allocation):
    self.width = allocation.width
    self.height = allocation.height

  def on_self_expose_event(self, widget, event):
    ctx = widget.bin_window.cairo_create()  
    if self.back_ground_image:
      self.back_ground_image.render(ctx)
    for box in self.projectdata.boxes:
      if self.page != box.page:
        continue
      if box.hilight:
        (r,g,b,a)=(0.9,0.2,0.4, 0.005)
      else:
        (r,g,b,a)=(1,0.5,0.5, 0.1)
      ctx.set_source_rgba(r,g,b,a)
      ctx.new_path()
      x1=self.projectdata.get_grid_coordinate_by_id(box.x_1)
      x2=self.projectdata.get_grid_coordinate_by_id(box.x_2)
      width=x2-x1
      y1=self.projectdata.get_grid_coordinate_by_id(box.y_1)
      y2=self.projectdata.get_grid_coordinate_by_id(box.y_2)
      height=y2-y1
      ctx.move_to(x1, y1)                      
      ctx.rel_line_to(width, 0)       
      ctx.rel_line_to(0, height)      
      ctx.rel_line_to(-width, 0)  
      ctx.close_path()                       
      ctx.fill()

      a=0.8
      ctx.set_source_rgba(r,g,b,a)
      ctx.new_path()                         
      ctx.move_to(x1, y1)                      
      ctx.rel_line_to(width, 0)       
      ctx.rel_line_to(0, height)      
      ctx.rel_line_to(-1 * width, 0)  
      ctx.close_path()                       
      ctx.stroke()


      if box.hilight:
        a=0.5
        ctx.set_source_rgba(r,g,b,a)
        ctx.new_path()                         
        ctx.move_to(x1, y1)                      
        ctx.rel_line_to(width, height)       
        ctx.stroke()

      w=int(width*2/3)
      d=-int(width/10)
      dy=int(width/6)
      if box.valign==BoxData.VALIGN_TOP:
        y=y1
      elif box.valign==BoxData.VALIGN_BOTTOM:
        y=y2
        dy=-dy
      else:
        y=y1+height/6

      if box.halign==BoxData.HALIGN_LEFT:
        x=x1
        dd=0
      elif box.halign==BoxData.HALIGN_RIGHT:
        x=x2
        w=-w
        d=-d
        dd=0
      else:
        x=x1+width/6
        dd=-d

      a=0.8
      ctx.set_source_rgba(r,g,b,a)
      ctx.new_path()                         
      ctx.move_to(x,y)                      
      ctx.rel_line_to(w, 0)       
      ctx.rel_line_to(-d, dy)      
      ctx.rel_line_to(d, dy)      
      ctx.rel_line_to(-d, dy)      
      ctx.rel_line_to(d, dy)      
      ctx.rel_line_to(-w, 0)  
      ctx.rel_line_to(-dd, -dy)      
      ctx.rel_line_to(dd, -dy)      
      ctx.rel_line_to(-dd, -dy)      
      ctx.rel_line_to(dd, -dy)      
      ctx.stroke()

      a=0.05
      ctx.set_source_rgba(r,g,b,a)
      ctx.new_path()
      ctx.move_to(x,y)
      ctx.rel_line_to(w, 0)       
      ctx.rel_line_to(-d, dy)      
      ctx.rel_line_to(d, dy)      
      ctx.rel_line_to(-d, dy)      
      ctx.rel_line_to(d, dy)      
      ctx.rel_line_to(-w, 0)  
      ctx.rel_line_to(-dd, -dy)      
      ctx.rel_line_to(dd, -dy)      
      ctx.rel_line_to(-dd, -dy)      
      ctx.rel_line_to(dd, -dy)      
      ctx.close_path()                       
      ctx.fill()


      (r,g,b,a)=(0.3, 0.3, 0.6,1.0)
      ctx.set_source_rgba(r,g,b,a)
      ctx.select_font_face('Serif', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
      ctx.set_font_size(12)
      ctx.move_to(x1, y2)
      ctx.show_text(box.name)

class Bar(gtk.DrawingArea):
  def __init__(self,direction,margin):
    gtk.DrawingArea.__init__(self)
    self.width = self.height = 0
    self.red=0.5
    self.green=0.5
    self.blue=0.1
    self.alpha=0.5
    self.direction=direction
    self.connect('size-allocate', self.on_self_size_allocate)
    self.connect('expose-event', self.on_self_expose_event)
    self.margin=margin
    
  def on_self_size_allocate(self, widget, allocation):
    self.width = allocation.width
    self.height = allocation.height
    
  def on_self_expose_event(self, widget, event):
    ctx = widget.window.cairo_create()
    ctx.set_source_rgba(self.red, self.green, self.blue, self.alpha)
    if self.direction & BarOnLayout.MASK_VIRTICAL_BAR:
      ctx.set_source_rgba(self.red, self.green, self.blue, self.alpha)
      ctx.new_path()                         
      ctx.move_to(0, self.margin)
      ctx.rel_line_to(0,self.height-self.margin)      
      ctx.rel_line_to(self.width, 0)       
      ctx.rel_line_to(0,-self.height+self.margin)      
      ctx.close_path()                       
      ctx.fill() 
      
      ctx.set_source_rgba(0,0,0,1)
      ctx.new_path()                         
      ctx.move_to(0, 0)                      
      ctx.rel_line_to(0,self.height)      
      ctx.rel_line_to(1, 0)       
      ctx.rel_line_to(0,-self.height)      
      ctx.close_path()                       
      ctx.fill()
    else:
      ctx.new_path()                         
      ctx.move_to(self.margin, 0)                      
      ctx.rel_line_to(self.width-self.margin, 0)       
      ctx.rel_line_to(0,self.height)      
      ctx.rel_line_to(-self.width+self.margin, 0)  
      ctx.close_path()                       
      ctx.fill() 
      


      ctx.set_source_rgba(0,0,0,1)
      ctx.new_path()                         
      ctx.move_to(0, 0)                      
      ctx.rel_line_to(self.width, 0)       
      ctx.rel_line_to(0,1)      
      ctx.rel_line_to(-self.width, 0)  
      ctx.close_path()                       
      ctx.fill() 


class SpinButtonForBarOnLayout(gtk.SpinButton):
  def __init__(self,adj_max,a,b):
    adj=gtk.Adjustment(value=0,lower=0,upper=adj_max, step_incr=-1)
    gtk.SpinButton.__init__(self,adj,a,b)
    self.set_width_chars(5)
    self.set_alignment(1.0)
    self.connect("changed", self.move_bar)
    self.bars=[]
    self.current_bar=None
    
  def append_bar(self,bar):
    self.bars.append(bar)
#    self.set_current_bar(bar)
    
  def set_current_bar(self,bar):
    if bar != self.current_bar:      
      self.current_bar=bar
      if bar.direction & bar.MASK_VIRTICAL_BAR:
        self.set_value(bar.x)
      else:
        self.set_value(bar.y)
      
  def move_bar(self,widget):
    if self.current_bar != None:
      self.current_bar.move_to_value(get_int_from_spinbutton(self))

class BarOnLayout(gtk.EventBox):
  MASK_VIRTICAL_BAR=2
  MASK_OPPOSIT_DIRECTION=1
  LINEWIDTH=3
  def __init__(self,direction,max_x,max_y,spinbuttonforbar,griddata):
    gtk.EventBox.__init__(self)
    self.x=0
    self.y=0
    self.direction=direction
    self.max_x=max_x
    self.max_y=max_y

    self.spinbutton=spinbuttonforbar
    self.spinbutton.append_bar(self)
    self.griddata=griddata

    self.label=gtk.Label()
    self.label.set_markup(str(self.griddata.id))
    self.label.show()

    if direction & self.MASK_VIRTICAL_BAR:
      self.height=max_y
      self.width=self.LINEWIDTH
      self.margin=(13+20*griddata.id)%self.height

    else:
      self.width=max_x
      self.height=self.LINEWIDTH
      self.margin=(13+20*griddata.id)%self.width
    drawingarea = Bar(direction,self.margin)
    drawingarea.set_size_request(self.width,self.height)
    self.add(drawingarea)
    drawingarea.show()
    self.draging=False
    self.connect("motion_notify_event", self.motion_notify_event)
    self.connect("button_press_event", self.button_press_event)
    self.connect("button_release_event", self.button_release_event)

  def get_label(self):
    return self.label
  
  def get_spinbutton(self):
    return self.spinbutton

  def move_to_value_of_spinbutton(self,widget):
    self.move_to_value(get_int_from_spinbutton(self.spinbutton))

  def move_to_value(self,v):
    if self.draging:
      return 
    if self.direction & self.MASK_VIRTICAL_BAR:
      if v != self.x:
        self.move_horizontal(v)
    else:
      if v != self.y:
        self.move_virtical(v)

  def move_to(self,x, y):
    if self.direction & self.MASK_OPPOSIT_DIRECTION:
      if self.direction & self.MASK_VIRTICAL_BAR:
        self.x=x
        x=self.x-self.width
        self.y=y
      else:
        self.x=x
        self.y=y
        y=self.y-self.height
    else:
      self.x=x
      self.y=y
    self.parent.move(self, x, y)
    if self.spinbutton:
      self.spinbutton.set_current_bar(self)
      if self.direction & self.MASK_VIRTICAL_BAR:
        self.spinbutton.set_value(self.x)
      else:
        self.spinbutton.set_value(self.y)
    if self.griddata.is_horizontal:
      self.griddata.value=self.y
      self.parent.move(self.label, x+self.margin, self.y+self.LINEWIDTH)
    else:
      self.griddata.value=self.x
      self.parent.move(self.label, self.x+self.LINEWIDTH, y+self.margin)
    


  def move_virtical(self,y):
    if self.direction & self.MASK_OPPOSIT_DIRECTION and self.direction & self.MASK_VIRTICAL_BAR==0:
      self.y=int(y)
      y=self.y-self.height
    else:
      self.y=int(y)
      y=self.y
    if self.spinbutton:
      self.spinbutton.set_current_bar(self)
      self.spinbutton.set_value(self.y)
    self.parent.move(self,self.x,y)
    self.parent.move(self.label, self.x+self.margin, y+self.LINEWIDTH)
  def move_horizontal(self,x):
    if self.direction & self.MASK_OPPOSIT_DIRECTION and self.direction & self.MASK_VIRTICAL_BAR:
      self.x=int(x)
      x=self.x-self.width
    else:
      self.x=int(x)
      x=self.x
    if self.spinbutton:
      self.spinbutton.set_current_bar(self)
      self.spinbutton.set_value(self.x)
    self.parent.move(self, x, self.y)
    self.parent.move(self.label, x+self.LINEWIDTH, self.y+self.margin)
  def button_press_event(self,widget, event):
    self.spinbutton.set_current_bar(self)
    if event.button == 1:
      self.draging=True
      if self.direction & self.MASK_OPPOSIT_DIRECTION:
        self.margin_x = event.x-self.width
        self.margin_y = event.y-self.height
      else:
        self.margin_x = event.x
        self.margin_y = event.y
      self.margin_x =self.margin_x-int(self.parent.get_hadjustment().get_value())

      self.margin_y =self.margin_y-int(self.parent.get_vadjustment().get_value())

      state = event.state
    return True

  def button_release_event(self,widget, event):
    if not self.draging:
      return True
    x, y, state = self.parent.window.get_pointer()
    if self.direction & self.MASK_VIRTICAL_BAR:
      self.move_horizontal(x-self.margin_x)
    else:
      self.move_virtical(y-self.margin_y)

    if self.direction & self.MASK_VIRTICAL_BAR:
      if self.x<0:
        self.move_horizontal(0)
      if self.max_x<self.x:
        self.move_horizontal(self.max_x)
    else:
      if self.y<0:
        self.move_virtical(0)
      if self.max_y<self.y:
        self.move_virtical(self.max_y)
    self.margin_x = 0
    self.margin_y = 0
    self.draging=False
    return True

  def motion_notify_event(self,widget, event):
    if not self.draging:
      return True
    x, y, state = self.parent.window.get_pointer()
    if state & gtk.gdk.BUTTON1_MASK:
      if self.direction & self.MASK_VIRTICAL_BAR:
        self.move_horizontal(x-self.margin_x)
      else:
        self.move_virtical(y-self.margin_y)
    return True





##################
class BoxDataDialog(gtk.Dialog):
  def __init__(self,title=None, parent=None, flags=0, buttons=None,boxdata=None,message="",projectdata=None):
    gtk.Dialog.__init__(self,title,parent,flags,buttons)
    self.area=BoxDataEntryArea(boxdata,message,projectdata)
    self.vbox.pack_start(self.area.get_box())

  def get_boxdata(self):
    return self.area.update_and_get_boxdata()

class RulerDialog(gtk.Dialog):
  def __init__(self,title=None, parent=None, flags=0, buttons=None,projectdata=None,xrulers_lr=[],yrulers_ud=[],xx=[],yy=[],p=0):
    gtk.Dialog.__init__(self,title,parent,flags,buttons)
    self.area=LayoutOverBoxesWithRulersArea(projectdata,xrulers_lr,yrulers_ud,xx,yy,p)
    self.vbox.pack_start(self.area.get_box())
    (w,h)=projectdata.get_default_dialog_size()
    self.resize(w,h)

  def get_coordinates(self):
    return self.area.get_coordinates()

  def refresh_preview(self):
    if self.area:
      self.area.refresh_preview()

class HoganDialog(gtk.Dialog):
  def __init__(self,title=None, parent=None, flags=0, buttons=None, projectdata=None,p=0):
    gtk.Dialog.__init__(self,title,parent,flags,buttons)
    self.area=LayoutOverBoxesWithHoganArea(projectdata,p)
    self.vbox.pack_start(self.area.get_box())
    (w,h)=projectdata.get_default_dialog_size()
    self.resize(w,h)

  def get_coordinates(self):
    return self.area.get_coordinates()

  def refresh_preview(self):
    if self.area:
      self.area.refresh_preview()


class LayoutOverBoxesWithRulersArea:
  HEIGHT = 600
  WIDTH = 600

  def __init__(self,projectdata,x_rulers_lr,y_rulers_ud,xx,yy,p):
    self.projectdata=projectdata
    box = gtk.VBox(False,0)
    box.show()
    table = gtk.Table(2, 2, False)
    table.show()
    box.pack_start(table, True, True, 0)
    layout = LayoutOverBoxes(self.projectdata)
    self.layout = layout
    self.layout.set_page(p)

    layout.set_size(self.projectdata.lwidth, self.projectdata.lheight)
    layout.connect("size-allocate", self.layout_resize)
    layout.show()
    table.attach(layout, 0, 1, 0, 1, gtk.FILL|gtk.EXPAND,
                 gtk.FILL|gtk.EXPAND, 0, 0)
    vScrollbar = gtk.VScrollbar(None)
    vScrollbar.show()
    table.attach(vScrollbar, 1, 2, 0, 1, gtk.FILL|gtk.SHRINK,
                 gtk.FILL|gtk.SHRINK, 0, 0)
    hScrollbar = gtk.HScrollbar(None)
    hScrollbar.show()
    table.attach(hScrollbar, 0, 1, 1, 2, gtk.FILL|gtk.SHRINK,
                 gtk.FILL|gtk.SHRINK,
                 0, 0)	
    vAdjust = layout.get_vadjustment()
    vScrollbar.set_adjustment(vAdjust)
    hAdjust = layout.get_hadjustment()
    hScrollbar.set_adjustment(hAdjust)
    
    coordinate_hbox=gtk.HBox(spacing=20)

    hbox=gtk.HBox()
    coordinate_hbox.add(hbox)
    label=gtk.Label()
    hbox.add(label)
    label.set_markup("page: ")
    adj = gtk.Adjustment(value=p, lower=0,upper=self.projectdata.n_pages-1, step_incr=-1)
    entry=gtk.SpinButton(adj, 0, 0)
    entry.connect("changed", self.on_page_changed_event)
    hbox.add(entry)



    max_x=self.projectdata.lwidth
    max_y=self.projectdata.lheight

    self.x_rulers=[]
    if x_rulers_lr != []:
      hbox=gtk.HBox()
      coordinate_hbox.add(hbox)

      label=gtk.Label()
      hbox.add(label)
      label.set_markup("x: ")
      for ruler_i_is_left in x_rulers_lr:
        if ruler_i_is_left:
          bar=BarOnLayout(3,max_x,max_y)
        else:
          bar=BarOnLayout(2,max_x,max_y)
        self.x_rulers.append(bar)
        bar.show()
        self.layout.add(bar)

        
        hbox.add(bar.get_spinbutton())


    self.y_rulers=[]
    if y_rulers_ud != []:
      hbox=gtk.HBox()
      coordinate_hbox.add(hbox)

      label=gtk.Label()
      hbox.add(label)
      label.set_markup("y: ")
      for ruler_i_is_down in y_rulers_ud:
        if ruler_i_is_down:
          bar=BarOnLayout(1,max_x,max_y)
        else:
          bar=BarOnLayout(0,max_x,max_y)
        self.y_rulers.append(bar)
        bar.show()
        self.layout.add(bar)
        hbox.add(bar.get_spinbutton())

    coordinate_hbox.show_all()
    box.pack_start(coordinate_hbox, False, False, 0)

    
    self.move_rulers(xx,yy)

    hbox=gtk.HBox()
    hbox.add(box)
    hbox.show_all()
    self.box=hbox

  def refresh_preview(self):
    self.layout.refresh_preview()

  def get_box(self):
    return self.box

  def move_rulers(self,xx,yy):
    for (ruler,xi) in zip(self.x_rulers,xx):
      ruler.move_to(xi,0)
    for (ruler,yi) in zip(self.y_rulers,yy):
      ruler.move_to(0,yi)

  def layout_resize(self, widget, event):
    x, y, width, height = widget.get_allocation()
    if width > self.projectdata.lwidth or height > self.projectdata.lheight:
      lwidth = max(width, self.projectdata.lwidth)
      lheight = max(height, self.projectdata.lheight)
      widget.set_size(lwidth, lheight)

  def on_page_changed_event(self,widget):
    self.layout.set_page(get_int_from_spinbutton(widget))


#  def get_coordinates(self):
#    return ([ruler.x for ruler in self.x_rulers],[ruler.y for ruler in self.y_rulers],self.layout.page)

class LayoutOverBoxesWithHoganArea:
  HEIGHT = 600
  WIDTH = 600

  def __init__(self,projectdata,p):
    self.projectdata=projectdata
    
    box = gtk.VBox(False,0)
    box.show()
    table = gtk.Table(2, 2, False)
    table.show()
    box.pack_start(table, True, True, 0)
    layout = LayoutOverBoxes(self.projectdata)
    self.layout = layout
    self.layout.set_page(p)

    layout.set_size(self.projectdata.lwidth, self.projectdata.lheight)
    layout.connect("size-allocate", self.layout_resize)
    layout.show()
    table.attach(layout, 0, 1, 0, 1, gtk.FILL|gtk.EXPAND,
                 gtk.FILL|gtk.EXPAND, 0, 0)
    vScrollbar = gtk.VScrollbar(None)
    vScrollbar.show()
    table.attach(vScrollbar, 1, 2, 0, 1, gtk.FILL|gtk.SHRINK,
                 gtk.FILL|gtk.SHRINK, 0, 0)
    hScrollbar = gtk.HScrollbar(None)
    hScrollbar.show()
    table.attach(hScrollbar, 0, 1, 1, 2, gtk.FILL|gtk.SHRINK,
                 gtk.FILL|gtk.SHRINK,
                 0, 0)	
    vAdjust = layout.get_vadjustment()
    vScrollbar.set_adjustment(vAdjust)
    hAdjust = layout.get_hadjustment()
    hScrollbar.set_adjustment(hAdjust)
    
    coordinate_hbox=gtk.HBox(spacing=20)
    self.coordinate_hbox=coordinate_hbox
    
    hbox=gtk.HBox()
    coordinate_hbox.add(hbox)
    label=gtk.Label()
    hbox.add(label)
    label.set_markup("page: ")
    adj = gtk.Adjustment(value=p, lower=0,upper=self.projectdata.n_pages-1, step_incr=1)
    entry=gtk.SpinButton(adj, 0, 0)
    entry.connect("changed", self.on_page_changed_event)
    hbox.add(entry)


    w=self.projectdata.lwidth
    h=self.projectdata.lheight
    self.spb=SpinButtonForBarOnLayout(max(w,h),0,0)
    hbox=gtk.HBox()
    self.coordinate_hbox.add(hbox)
    label=gtk.Label()
    hbox.add(label)
    label.set_markup("coordinate: ")
    hbox.add(self.spb)


    hbox = gtk.HButtonBox()
    coordinate_hbox.add(hbox)
    hbox.set_layout(gtk.BUTTONBOX_END)
    button = gtk.Button(stock=gtk.STOCK_ADD)
    hbox.add(button)
    self.button_edit=button
    button.connect('clicked', self.add_new_x_ruler_onclick)
    button = gtk.Button(stock=gtk.STOCK_ADD)
    hbox.add(button)
    self.button_edit=button
    button.connect('clicked', self.add_new_y_ruler_onclick)

    self.rulers=[]

    coordinate_hbox.show_all()
    box.pack_start(coordinate_hbox, False, False, 0)

    hbox=gtk.HBox()
    hbox.add(box)
    hbox.show_all()
    self.box=hbox
    
  def add_ruler(self,griddata):
    w=self.projectdata.lwidth
    h=self.projectdata.lheight
    if griddata.is_horizontal:
      bar=BarOnLayout(1,w,h,self.spb,griddata)
    else:
      bar=BarOnLayout(2,w,h,self.spb,griddata)
    self.rulers.append(bar)
    bar.show()
    self.layout.add(bar)
    self.layout.add(bar.get_label())
    bar.move_to_value(griddata.value)
    return bar
  
  def add_new_x_ruler_onclick(self,widget):
    w=self.projectdata.lwidth
    g=GridData(0,w//2,False)
    bar=self.add_ruler(g)
    
  def add_new_y_ruler_onclick(self,widget):
    h=self.projectdata.lheight
    g=GridData(0,h//2,True)
    bar=self.add_ruler(g)

    
  
  def refresh_preview(self):
    self.layout.refresh_preview()

  def get_box(self):
    return self.box

  def layout_resize(self, widget, event):
    x, y, width, height = widget.get_allocation()
    if width > self.projectdata.lwidth or height > self.projectdata.lheight:
      lwidth = max(width, self.projectdata.lwidth)
      lheight = max(height, self.projectdata.lheight)
      widget.set_size(lwidth, lheight)

  def on_page_changed_event(self,widget):
    self.layout.set_page(get_int_from_spinbutton(widget))

  def get_coordinates(self):
    return ([ruler.x for ruler in self.rulers if not ruler.griddata.is_horizontal],[ruler.y for ruler in self.y_rulers if  ruler.griddata.is_horizontal],self.layout.page)


class ProjectData:
  HEIGHT = 600
  WIDTH = 600
  def __init__(self,uri):
    self.set_path_and_document(uri)
    
  def set_path_and_document(self,uri):    
    if uri:
      self.document = poppler.document_new_from_file(uri,None)
      p=urlparse.urlparse(uri)
      path=urllib.unquote(p.path)
      self.bgimagefullpath=path
      (self.destdir,self.bgimagepath)=os.path.split(path)
      basefilename=os.path.splitext(self.bgimagepath)[0]
      self.stylename=basefilename
#      self.samplepath=basefilename+".tex"
      self.samplepath="sample.tex"
      self.samplebase="sample"
    else:
      self.document=None
    self.boundingboxes=[]
    if self.document:
      self.n_pages = self.document.get_n_pages()
      width = 0
      height = 0
    
      self.pages=[ None for i in range(self.n_pages)]
      for i in range(self.n_pages):
        (w,h) =self.document.get_page(i).get_size()
        self.boundingboxes.append((0,0,w,h))
        if width<w:
          width=w
        if height<h:
          height=h

      self.lwidth = int(width)
      self.lheight = int(height)
      
    else:
      self.n_pages=10000
      self.lwidth = self.WIDTH
      self.lheight = self.HEIGHT


    self.boxes=[]
    self.grids=[]
    self.set_default_dialog_size((self.lwidth,self.lheight))

  def add_boxdata(self,boxdata):
    self.boxes.append(boxdata)

  def add_grid(self,grid_data):
    self.grids_h.append(grid_data)

  def get_griddata_by_id(self,id):
    for griddata in self.grids:
      if griddata.id==id:
        return griddata
    return None

  def get_grid_coordinate_by_id(self,id):
    g=self.get_griddata_by_id(id)
    if g==None:
      return 0
    
    return griddata.value


  def pop_boxdata_by_id(self,id):
    for (i,boxdata) in enumerate(self.boxes):
      if boxdata.id==id:
        box=self.boxes.pop(i)
        return box
    return None

  def get_boxdata_by_id(self,id):
    for boxdata in self.boxes:
      if boxdata.id==id:
        return boxdata
    return None

  def get_page(self,page):
    if self.pages[page]:
      return self.pages[page]
    else:
      self.pages[page]=self.document.get_page(page)
      return self.pages[page]

  def output_to_zipfile(self,destzip,rootdir):
    print "writing imagefiles...."
    afd=applicationFormData(self.boxes,self.bgimagepath,self.boundingboxes)
    afd.create_bgimage_file(self.bgimagefullpath,destzip,rootdir)

    print "writing the style file...."
    stypath=os.path.join(rootdir,self.stylename+".sty")
    inf=zipfile.ZipInfo(stypath)
    destzip.writestr(inf,afd.get_style_code())

    print "writing a sample file...."
    samplepath=os.path.join(rootdir,self.samplepath)
    inf=zipfile.ZipInfo(samplepath)
    destzip.writestr(inf,afd.get_sample_code(self.stylename))

    print "writing Makefile...."
    makefilepath=os.path.join(rootdir,"Makefile")
    inf=zipfile.ZipInfo(makefilepath)
    destzip.writestr(inf,afd.get_sample_makefile(self.samplebase))

    for inf in destzip.infolist():
      inf.external_attr = 0755 << 16L
      inf.create_system = 0
    destzip.close()
    print "done."

  def get_default_dialog_size(self):
    return self.dialogsize
  
  def set_default_dialog_size(self,s):
    self.dialogsize=s

class AFMMainArea:
  def __init__(self,projectdata):
    self.projectdata=projectdata
    self.current_coordinate=None    
    self.my_clip_board=((0,0),[])
    
    self.box=gtk.VBox()
    listarea=BoxDataListArea(self)
    self.box.pack_start(listarea.get_vbox())
    self.listarea=listarea
    (button_new,button_remove,button_edit,button_copy,button_paste)=listarea.get_buttons()
    button_new.connect('clicked', self.on_click_new)
    button_remove.connect('clicked', self.on_click_remove)
    button_edit.connect('clicked', self.on_click_edit)
    button_copy.connect('clicked', self.on_click_copy)
    button_paste.connect('clicked', self.on_click_paste)


    hbbox = gtk.HButtonBox() 
    listarea.get_vbox().pack_start(hbbox,expand=False, fill=False)
    hbbox.set_layout(gtk.BUTTONBOX_END)
    button = gtk.Button(stock=gtk.STOCK_SAVE_AS)
    button.connect('clicked', self.on_click_save_as)
    hbbox.add(button)
    hbbox.show_all()

    self.box.show_all()
    
    self.open_preview_dialog()
    
  def open_preview_dialog(self):
    (p,x,y,w,h)=self.get_current_coordinate()
    dialog=HoganDialog("Preview",None,
                       gtk.DIALOG_DESTROY_WITH_PARENT,
                       None,
                       self.projectdata,p)
    dialog.show()
    self.preview=dialog

  def get_current_coordinate(self):
    if self.current_coordinate:
      return self.current_coordinate
    else:
      p=0
      x=self.projectdata.lwidth//5
      w=self.projectdata.lwidth*3//5
      y=self.projectdata.lheight//7
      h=self.projectdata.lheight//6
      return (p,x,y,w,h)

#  def set_current_coordinate(self,boxdata):
#    self.current_coordinate=(boxdata.page,boxdata.x,boxdata.y,boxdata.width,boxdata.height)


  def get_box(self):
    return self.box

  def on_click_save_as(self,widget):
    dialog = gtk.FileChooserDialog('Select zip file to save.',None,
                                   action=gtk.FILE_CHOOSER_ACTION_SAVE,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
    dialog.set_current_folder(self.projectdata.destdir)
    dialog.set_current_name(self.projectdata.stylename+'-stylefile.zip')

    dialog.set_do_overwrite_confirmation(True)
    filter = gtk.FileFilter()
    filter.set_name("ZIP files")
    filter.add_mime_type("application/x-compress")
    filter.add_mime_type("application/x-zip-compressed")
    filter.add_mime_type("application/zip")
    filter.add_mime_type("application/x-zip")
    filter.add_pattern("*.zip")
    dialog.add_filter(filter)
    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    r = dialog.run()
    if r!=gtk.RESPONSE_ACCEPT:
      dialog.destroy()
      return
    destzipfilename=dialog.get_filename()
    dialog.destroy()
    print 'creating ', destzipfilename
    rootdir=os.path.splitext(os.path.basename(destzipfilename))[0]
    destzip=zipfile.ZipFile(destzipfilename,'w')
    self.projectdata.output_to_zipfile(destzip,rootdir)
    gtk.main_quit()

  def on_click_save(self,widget):
    rootdir='stylefile'
    destzip=zipfile.ZipFile(os.path.join(self.destdir,rootdir+'.zip'),'w')
    self.projectdata.output_to_zipfile(destzip,rootdir)
    gtk.main_quit()

  def refresh_preview(self):
      if self.preview:
        self.preview.refresh_preview()

  def on_click_new(self,widget):
    (p,x,y,w,h)=self.get_current_coordinate()
    boxdata=BoxData(p,0,2,1,3)    
    self.conform_and_add(boxdata)

  def conform_and_add(self,boxdata):
    title="New box."
    message="Add the following box:"
    boxdata=self.get_valid_boxdata_by_dialog(boxdata,title,message)
    if boxdata:
      self.listarea.append_boxdata(boxdata)
      self.projectdata.add_boxdata(boxdata)
      self.refresh_preview()
#      self.set_current_coordinate(boxdata)

  def on_click_remove(self,widget):
    (model,iteralist,boxids)=self.listarea.get_selected_ids()
    if not boxids:
      return
    for (itera,boxid,) in zip(iteralist,boxids):
      self.conform_and_remove_by_id(boxid,model,itera)

  def conform_and_remove_by_id(self,boxid,model,itera):
    if not boxid:
      return
    boxdata=self.projectdata.get_boxdata_by_id(boxid)
    title="Remove BOX."
    message="Remove the following box:"
    boxdata=self.get_valid_boxdata_by_dialog(boxdata,title,message)
    if boxdata:
      self.projectdata.pop_boxdata_by_id(boxid)
      self.refresh_preview()
      model.remove(itera)

  def on_click_edit(self,widget):
#    (model,itera,boxid)=self.listarea.get_selected_id()
    (model,iteralist,boxids)=self.listarea.get_selected_ids()
    if not boxids:
      return
    for (itera,boxid,) in zip(iteralist,boxids):
      if not boxid:
        return
      boxdata=self.projectdata.get_boxdata_by_id(boxid)
      title="BOX id "+boxid
      message="Edit the following box:"
      boxdata=self.get_valid_boxdata_by_dialog(boxdata,title,message)
      if boxdata:
        self.projectdata.pop_boxdata_by_id(boxid)
        self.projectdata.add_boxdata(boxdata)
        self.refresh_preview()

        model.remove(itera)
        self.listarea.append_boxdata(boxdata)

        self.current_coordinate=(boxdata.page,boxdata.x,boxdata.y,boxdata.width,boxdata.height)

  def on_click_copy(self,widget):
    (model,iteralist,boxids)=self.listarea.get_selected_ids()
    if not boxids:
      return
    boxdata=[]
    for (itera,boxid,) in zip(iteralist,boxids):
      if boxid:
        b=self.projectdata.get_boxdata_by_id(boxid)
        if b:
          boxdata.append(b)
    if boxdata==[]:
      return
    dialog=gtk.MessageDialog(type=gtk.MESSAGE_INFO,buttons = gtk.BUTTONS_OK_CANCEL,message_format="To copy selected box(es), choose the base point of the box(es).")
    r=dialog.run()
    if r == gtk.RESPONSE_OK:
      xx=[boxdata[0].x]
      yy=[boxdata[0].y]
      p=boxdata[0].page
      rulerdialog = RulerDialog("Choose the base point",None,
                        gtk.DIALOG_MODAL,
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                         self.projectdata,
                         [True],[True],xx,yy,p)

      r2 = rulerdialog.run()
      self.projectdata.set_default_dialog_size(rulerdialog.get_size())
      if r2==gtk.RESPONSE_ACCEPT:
        self.my_clip_borad=(rulerdialog.get_coordinates(),boxdata)
      rulerdialog.destroy()
    else:
      pass
    dialog.destroy()

  def on_click_paste(self,widget):
    (base,boxdata)=self.my_clip_borad
    if not base:
      return 
    (xx,yy,p)=base
    dialog=gtk.MessageDialog(type=gtk.MESSAGE_INFO,buttons = gtk.BUTTONS_OK_CANCEL,message_format="Choose the base point to paste.")
    r=dialog.run()
    if r == gtk.RESPONSE_OK:
      rulerdialog = RulerDialog("Choose the base point",None,
                        gtk.DIALOG_MODAL,
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                         self.projectdata,
                         [True],[True],xx,yy,p)
      r2 = rulerdialog.run()
      self.projectdata.set_default_dialog_size(rulerdialog.get_size())
      if r2==gtk.RESPONSE_ACCEPT:
        destbase=rulerdialog.get_coordinates()
        rulerdialog.destroy()
        (dxx,dyy,dp)=destbase
        dx=dxx[0]-xx[0]
        dy=dyy[0]-yy[0]
        for bi in boxdata:
          bbi=bi.get_similar_boxdata()
          bbi.x=bbi.x+dx
          bbi.y=bbi.y+dy
          self.conform_and_add(bbi)
      else:
        rulerdialog.destroy()
    else:
      pass
    dialog.destroy()


  def get_boxdata_by_dialog(self,boxdata,title,message):
    dialog=BoxDataDialog(title,None,
                        gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL,
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                         boxdata,message,self.projectdata)

    r = dialog.run()
    if r==gtk.RESPONSE_ACCEPT:
      boxdata=dialog.get_boxdata()
    else:
      boxdata=None
    dialog.destroy()
    return boxdata

  def get_valid_boxdata_by_dialog(self,boxdata,title,message):
    boxdata=self.get_boxdata_by_dialog(boxdata,title,message)
    while not self.is_valid_boxdata(boxdata):
      boxdata=self.get_boxdata_by_dialog(boxdata,title,message)
    return boxdata

  def is_valid_boxdata(self,boxdata):
    if boxdata:
      return True
    else:
      return True
###

class Afmmain:
  def __init__(self,uri):
    self.projectdata=ProjectData(uri)
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_default_size(360, 300)
    self.window.connect("destroy", lambda w: gtk.main_quit())
    self.window.show()
    layout = AFMMainArea(ProjectData(uri))
    self.window.add(layout.get_box())

  def get_uri_of_base_pdf_by_dialog(self):
    dialog = gtk.FileChooserDialog('Choose pdf file.',
                                   self.window,
                                   buttons=(gtk.STOCK_CANCEL,
                                            gtk.RESPONSE_REJECT,
                                            gtk.STOCK_OPEN,
                                            gtk.RESPONSE_ACCEPT))
    r = dialog.run()
    if r==gtk.RESPONSE_ACCEPT:
      uri=dialog.get_uri()
    else:
      uri==None
    dialog.destroy()
    return uri





if __name__ == "__main__":
  uri=None
  if len(sys.argv)>1 :
    uri='file://'+urllib.pathname2url(os.path.abspath(sys.argv[1]))
  if not uri:
    dialog = gtk.FileChooserDialog('Choose pdf file.',None,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
    filter = gtk.FileFilter()
    filter.set_name("PDF files")
    filter.add_mime_type("application/pdf")
    filter.add_mime_type("application/x-pdf")
    filter.add_pattern("*.pdf")
    dialog.add_filter(filter)
    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    r = dialog.run()
    if r==gtk.RESPONSE_ACCEPT:
      uri=dialog.get_uri()
      print uri
      dialog.destroy()
    else:
      dialog.destroy()

  if uri:
    Afmmain(uri)
    gtk.main()

