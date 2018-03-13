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
import json

def get_int_from_spinbutton(spinbutton):
  if spinbutton.get_text():
    return int(spinbutton.get_text())
  else:
    return spinbutton.get_value_as_int()



#####################################################
class applicationFormData:
  def int2alphabet(self,n):
    r=""
    while n>19:
      r=chr(ord('A')+(n%20))+r
      n=(n-(n%20))//20
    return  chr(ord('A')+n)+r
  
  def create_bgimage_file(self,pdffullpath,destzip,rootdir):    
    destzip.write(pdffullpath,os.path.join(rootdir,self.pdffilename()))

  def __init__(self,projectdata):
    self.projectdata=projectdata    
    self.UNITLENGTH=1.0
    self.XMARGIN=1.0
    self.YMARGIN=1.0
    self.PREFIX_SETVARAT="@set@temp@vars"
    self.SUFFIX_SETVARAT="@nu"
    self.PREFIX_ROUNDRECTANGLEAT=""
    self.SUFFIX_ROUNDRECTANGLEAT="@roundrectangle@nu"
    self.PREFIX_TABLEAT="@table@"
    self.SUFFIX_TABLEAT="@nu"
    self.PREFIX_TABLEROWAT="@table@row@"
    self.SUFFIX_TABLEROWAT="@nu"
    self.PREFIX_TABLE="tableform"
    self.SUFFIX_TABLE=""
    self.PREFIX_TABLECOL="col"
    self.SUFFIX_TABLECOL=""
    self.PREFIX_TABLECOLAT="@table@col@"
    self.SUFFIX_TABLECOLAT="@nu"
    self.FINALROW_HOOK_NAME="\\final@row@hook@nu"
    self.bgfilename=self.projectdata.bgimagepath

  def get_boundingboxstring(self,n):
    (ltx,lty,rbx,rby)=self.projectdata.boundingboxes[n]
    r=str(int(ltx))+' '+str(int(lty))+' '+str(int(rbx))+' '+str(int(rby))
    return r

  def dtppt2texpt(self,dtp_pt):
    return dtp_pt*(72.27)/(72.0)
  def dtppt2unitlength(self,dtp_pt):
    return self.dtppt2texpt(dtp_pt)/self.UNITLENGTH
  def dtppt2unitlength_as_str(self,dtp_pt):
    return str(self.dtppt2unitlength(dtp_pt))
  def setvarATname(self,name):
    return "\\"+self.PREFIX_SETVARAT+name+self.SUFFIX_SETVARAT
  def roundrectangleATname(self,name):
    return "\\"+self.PREFIX_ROUNDRECTANGLEAT+name+self.SUFFIX_ROUNDRECTANGLEAT
  def tablerowsATname(self,i):
    return "\\"+self.PREFIX_TABLEROWAT+self.int2alphabet(i)+self.SUFFIX_TABLEROWAT
  def tableATname(self,i):
    return  "\\"+self.PREFIX_TABLEAT+self.int2alphabet(i)+self.SUFFIX_TABLEAT
  def tablename(self,i):
    return self.PREFIX_TABLE+self.int2alphabet(i)+self.SUFFIX_TABLE
  def tablecolname(self,i):
    return "\\"+self.PREFIX_TABLECOL+self.int2alphabet(i)+self.SUFFIX_TABLECOL
  def tablecolATname(self,i):
    return "\\"+self.PREFIX_TABLECOLAT+self.int2alphabet(i)+self.SUFFIX_TABLECOLAT

  def form_table_sample(self,tabledata):
    r=""
    r=r +r'\begin{'
    r=r +self.tablename(tabledata.id_as_int)
    r=r +r'}'
    r=r +'\n'
    for ri in tabledata.table:
      for j,rij in enumerate(ri):
        boxdata=self.projectdata.get_boxdata_by_id(rij)
        r=r +r' '
        if boxdata.type==BoxData.TYPE_ENVIRONMENT:
          r=r +r'% '
        r=r + self.tablecolname(j)
        r=r +r'{'
        r=r +boxdata.sampletext
        r=r +r'}'+'\n'
      r=r +r'\nextrow'+'\n'
    r=r +r'\end{'
    r=r +self.tablename(tabledata.id_as_int)
    r=r +r'}'
    return r

  
  def form_sample(self,boxdata,as_comment):
    r=""
    if as_comment:
      r="% "
      bl='\n% '
    else:
      bl='\n'
    
    if boxdata.type==BoxData.TYPE_ENVIRONMENT:
      r=r +r'\begin{'
      r=r + boxdata.name
      r=r +r'}'
      r=r +bl
      r=r + boxdata.sampletext
      r=r +bl
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

  def formfrontenddef_env_l(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    r=r +r'\newenvironment{'
    r=r + name
    r=r +r'}{'
    r=r + self.setvarATname(name)
    r=r +r'\begin{put@@box@env@nu}}{\end{put@@box@env@nu}}'
    return r
  def formfrontenddef_env_r(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    r=r +r'\newenvironment{'
    r=r + name
    r=r +r'}{'
    r=r + self.setvarATname(name)
    r=r +r'\begin{put@@box@env@nu}\begin{flushright}}{\end{flushright}\end{put@@box@env@nu}}'
    return r
  def formfrontenddef_env_c(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    r=r +r'\newenvironment{'
    r=r +name
    r=r +r'}{'
    r=r + self.setvarATname(name)
    r=r +r'\begin{put@@box@env@nu}\begin{center}}{\end{center}\end{put@@box@env@nu}}'
    return r
  def formfrontenddef_com_l(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    r=r +r'\newcommand{'+"\\"
    r=r +name
    r=r +r'}[1]{'
    r=r + self.setvarATname(name)
    r=r +r'\put@@box@com@nu{#1}}'
    return r
  def formfrontenddef_com_c(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r +name
    r=r +r'}[1]{'
    r=r + self.setvarATname(name)
    r=r +r'\put@@box@com@nu{\begin{center}#1\end{center}}}'
    return r
  def formfrontenddef_com_r(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""

    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}[1]{'
    r=r + self.setvarATname(name)
    r=r +r'\put@@box@com@nu{\begin{flushright}#1\end{flushright}}}'
    return r
  def formfrontenddef_checkmark(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}{'
    r=r + self.setvarATname(name)
    r=r +r'\put@@box@checkmark@nu}'
    return r
  def formfrontenddef_strike(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}{'
    r=r + self.setvarATname(name)
    r=r +r'\put@@box@strike@nu}'
    return r
  def formfrontenddef_rule(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r +name
    r=r +r'}{'
    r=r + self.setvarATname(name)
    r=r +r'\put@@box@rule@nu}'
    return r
  def formfrontenddef_check_circle(self,name,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}{'
    r=r + self.roundrectangleATname(name)
    r=r +r'}'  
    return r
  
  def formfrontenddef(self,boxdata):
    r=[]
    as_comment=not(boxdata.type==BoxData.TYPE_ENVIRONMENT and boxdata.halign==BoxData.HALIGN_LEFT)
    r.append(self.formfrontenddef_env_l(boxdata.name,as_comment))
    
    as_comment=not(boxdata.type==BoxData.TYPE_ENVIRONMENT and boxdata.halign==BoxData.HALIGN_RIGHT)
    r.append(self.formfrontenddef_env_r(boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_ENVIRONMENT and boxdata.halign==BoxData.HALIGN_CENTER)
    r.append(self.formfrontenddef_env_c(boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_COMMAND and boxdata.halign==BoxData.HALIGN_LEFT)
    r.append(self.formfrontenddef_com_l(boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_COMMAND and boxdata.halign==BoxData.HALIGN_RIGHT)
    r.append(self.formfrontenddef_com_r(boxdata.name,as_comment))
    
    as_comment=not(boxdata.type==BoxData.TYPE_COMMAND and boxdata.halign==BoxData.HALIGN_CENTER)
    r.append(self.formfrontenddef_com_c(boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_CHECKMARK)
    r.append(self.formfrontenddef_checkmark(boxdata.name,as_comment))
    
    as_comment=not(boxdata.type==BoxData.TYPE_STRIKE)
    r.append(self.formfrontenddef_strike(boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_RULE)
    r.append(self.formfrontenddef_rule(boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_CHECK_CIRCLE)
    r.append(self.formfrontenddef_check_circle(boxdata.name,as_comment))
    return "\n".join(r)

  def setvardef(self,boxdata):
    (x1,x2,w,y1,y2,h)=self.projectdata.get_box_coordinate(boxdata)
    x=self.dtppt2unitlength_as_str(x1-self.XMARGIN)
    if boxdata.valign==BoxData.VALIGN_BOTTOM:
      y=-y2
      com_makebox_pos='bl'
    elif boxdata.valign==BoxData.VALIGN_CENTER:
      y=-y1-0.5*h
      com_makebox_pos='l'
    else:
      y=-y1
      com_makebox_pos='tl'
    y=self.dtppt2unitlength_as_str(y+self.YMARGIN)

    r=""
    r=r +r'\newcommand{'
    r=r + self.setvarATname(boxdata.name)
    r=r +r'}{\set@my@temp@var{'
    r=r + x
    r=r +r'}{'
    r=r + y
    r=r +r'}{'
    r=r + com_makebox_pos
    r=r +r'}{'
    r=r + self.dtppt2unitlength_as_str(w)    
    r=r +r'\unitlength}{'
    r=r + self.dtppt2unitlength_as_str(h)    
    r=r +r'\unitlength}}'

    return r
  
  def roundcircledef(self,boxdata):
    (x1,x2,w,y1,y2,h)=self.projectdata.get_box_coordinate(boxdata)
    put_roundrectangle_at=self.roundrectangleATname(boxdata.name)
    midx=self.dtppt2unitlength_as_str(x1+0.5*w-self.XMARGIN)
    midy=self.dtppt2unitlength_as_str(-y1-0.5*h+self.YMARGIN)
    round_R=min(w,h)
    if round_R >20:
      round_R=20
    round_r=int(0.5*round_R)
    round_wr=int(0.5*w)
    round_hr=int(0.5*h)
    round_w=round_wr-round_r
    round_h=round_hr-round_r

    r=""
    r=r +r'\newcommand{'
    r=r + put_roundrectangle_at
    r=r +r'}{'
    if round_R <5:
      r=r +r'\put('
      r=r + midx
      r=r +r','
      r=r + midy
      r=r +r'){'
      r=r +r'\makebox(0,0)[c]{$\circ$}'
      r=r +r'}'
    else:
      r=r +r'\put@roundCorners@nu{'
      r=r + midx
      r=r +r'}{'
      r=r + midy
      r=r +r'}{'      
      r=r + self.dtppt2unitlength_as_str(round_r*2)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_w)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_h)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_wr)
      r=r +r'}{'
      r=r + self.dtppt2unitlength_as_str(round_hr)
      r=r +r'}'
    r=r +r'}'
    return r
  def tablerowdef(self,tabledata):
    r=''
    l=len(tabledata.table)
    for i,ri in enumerate(tabledata.table):
      r=r +r'\def'
      r=r + self.tablerowsATname(i)
      r=r +r'{'
      for j,rij in enumerate(ri):
        r=r +r'\def'
        r=r + self.tablecolATname(j)
        r=r +r'{'
        r=r +'\\'
        r=r +self.projectdata.get_boxdata_by_id(rij).name 
        r=r +r'}'
      if l-1==i:
        r=r +r'\def\nextrow{'
        r=r +self.FINALROW_HOOK_NAME
        r=r + self.tablerowsATname(0)
        r=r +r'}'
      else:
        r=r +r'\def\nextrow{'
        r=r + self.tablerowsATname(i+1)
        r=r +r'}'
      r=r+r"}"+"\n"            
    r=r + self.tablerowsATname(0)
    return r
  

  def tablebackenddef(self,tabledata):
    r=""
    r=r +r'\newcommand{'
    r=r + self.tableATname(tabledata.id_as_int)
    r=r +r'}{%'+'\n'
    r=r + self.tablerowdef(tabledata)
    r=r +r"%"+'\n'+r"}"
    return r
  def tablefrontenddef(self,tabledata):
    r=""
    r=r +r'\newenvironment{'
    r=r +self.tablename(tabledata.id_as_int)
    r=r +r'}{'
    r=r + self.tableATname(tabledata.id_as_int)+"\n"
    r=r +r'\def'
    r=r+self.FINALROW_HOOK_NAME+"{}\n"
    for i,ri in enumerate(tabledata.table[0]):
        r=r +r'\def'
        r=r + self.tablecolname(i)
        r=r +r'{'
        r=r + self.tablecolATname(i)
        r=r +r'}'+"\n"
    r=r +r'}{}'
    return r

  def page_atfirst(self,n):
    return r'\pageNo'+self.int2alphabet(n)+r'AtFirst'
  def def_page_atfirst(self,n):
    return r'\newcommand{'+self.page_atfirst(n)+r'}{}'
  def pagename_frontend(self,n):
    return "pageNo"+self.int2alphabet(n)
  def pagename_none(self,n):
    return self.pagename_frontend(n)+"*"
  def pagename_pdf(self,n):
    return self.pagename_frontend(n)+"**"
  def pdffilename(self):
    return self.projectdata.bgimagepath

  def pagedef_pdf(self,n):
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
    return r

  def pagedef_woimage(self,n):
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
    return r
  
  def pagedef_frontend(self,n):
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
    return r

  def common_command(self):
    return r'''
% This file was created by AFM.
% The names of commands to put boxes may be just Box IDs.
% They are not good names to use.
% Please define commands to use as frontend.
%
% Please redefine the command \pageNoDAtFirst,
% if you want to do something whenever \begin{pageNoD} is called.
% Please redefine \baseuplength
% if you want to move background image up.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Definition of basic commands
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
\newcommand{\unitlength@nu}{'''+str(self.UNITLENGTH)+r'''truept}
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

\newcommand{\roundCorners@nu}[3][20]{\setlength\unitlength\unitlength@nu\put(#2,#3){\oval(#1,#1)[tr]}\put(-#2,#3){\oval(#1,#1)[tl]}\put(#2,-#3){\oval(#1,#1)[br]}\put(-#2,-#3){\oval(#1,#1)[bl]}}
\newcommand{\boxWithoutCorners@nu}[4]{\setlength\unitlength\unitlength@nu\put(0,#4){\line(1,0){#1}}\put(0,#4){\line(-1,0){#1}}\put(0,-#4){\line(1,0){#1}}\put(0,-#4){\line(-1,0){#1}}\put(#3,0){\line(0,1){#2}}\put(#3,0){\line(0,-1){#2}}\put(-#3,0){\line(0,1){#2}}\put(-#3,0){\line(0,-1){#2}}}

\newcommand{\put@roundCorners@nu}[7]{\setlength\unitlength\unitlength@nu\put(#1,#2){\roundCorners@nu[#3]{#4}{#5}\boxWithoutCorners@nu{#4}{#5}{#6}{#7}}}

\newcommand{\put@box@@nu}[4][]{\setlength\unitlength\unitlength@nu\put(#2,#3){\makebox(0,0)[#1]{#4}}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Definition of commands to put boxes by gloval variables.
\newcommand{\my@temp@var@x}{}
\newcommand{\my@temp@var@y}{}
\newcommand{\my@temp@var@p}{}
\newlength{\my@temp@var@w}
\newlength{\my@temp@var@h}
\newbox{\MyBlackBox@nu}
\newcommand{\set@my@temp@var}[5]{\def\my@temp@var@x{#1}\def\my@temp@var@y{#2}\def\my@temp@var@p{[#3]}\setlength{\my@temp@var@w}{#4}\setlength{\my@temp@var@h}{#5}}

\newenvironment{put@@box@env@nu}{\begin{lrbox}{\MyBlackBox@nu}\begin{minipage}[c]{\my@temp@var@w}}{\end{minipage}\end{lrbox}\expandafter\put@box@@nu\my@temp@var@p{\my@temp@var@x}{\my@temp@var@y}{\usebox{\MyBlackBox@nu}}}
\newcommand{\put@@box@com@nu}[1]{\expandafter\put@box@@nu\my@temp@var@p{\my@temp@var@x}{\my@temp@var@y}{\begin{minipage}[c]{\my@temp@var@w}#1\end{minipage}}}
\newcommand{\put@@box@rule@nu}{\put@@box@com@nu{\rule{\my@temp@var@w}{\my@temp@var@h}}}
\newcommand{\put@@box@strike@nu}{\put@@box@com@nu{\rule[0.22\my@temp@var@h]{\my@temp@var@w}{0.1666\my@temp@var@h}\kern -\my@temp@var@w\rule[0.6\my@temp@var@h]{\my@temp@var@w}{0.1666\my@temp@var@h}\rule{0pt}{\my@temp@var@h}}}
\newcommand{\put@@box@checkmark@nu}{\expandafter\put@box@@nu\my@temp@var@p{\my@temp@var@x}{\my@temp@var@y}{\begin{minipage}[c]{\my@temp@var@w}\centering$\checkmark$\end{minipage}}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
  
  def get_style_code(self):
    r="%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+self.common_command()
    r=r+"%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Definition of pages."

    page_atfirst=""
    page_def=""
    form_front=""

    for i in self.projectdata.get_pages_with_boxdata():
      page_def=page_def+"\n"+self.pagedef_frontend(i)
      page_def=page_def+"\n"+self.pagedef_woimage(i)
      page_def=page_def+"\n"+self.pagedef_pdf(i)
      page_atfirst=page_atfirst+"\n"+self.def_page_atfirst(i)
      form_front=form_front+"\n% page "+str(i+1)+" i.e.," +self.int2alphabet(i)
      for boxdata in self.projectdata.x_boxdata_in_the_page(i):
        form_front=form_front+"\n\n"+self.setvardef(boxdata)
        form_front=form_front+"\n"+self.roundcircledef(boxdata)
        form_front=form_front+"\n\n"+self.formfrontenddef(boxdata)
        form_front=form_front+"\n"
        
    table_backend=""
    table_front=""
    for tabledata in self.projectdata.tables:
      table_backend=table_backend+"\n"+self.tablebackenddef(tabledata)
      table_front=table_front+"\n"+self.tablefrontenddef(tabledata)
    r=r+page_def
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+table_backend
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Definition of each box\n"
    r=r+"% Set vars for x, y, pos, width, height.\n"

    r=r+form_front
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+page_atfirst
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+table_front
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    return r


  def get_sample_makefile(self,sample_file,style_file):
    r="LATEX=latex\nDVI2PDF=dvipdfmx\n"
    r=r+"STYLEFILE="+style_file+"\n\n"
    
    r=r+"TEXFILE="+sample_file+"\n\n"
    r=r+"all: pdf\ndvi: ${TEXFILE}.dvi\npdf: ${TEXFILE}.pdf\n\n"
    r=r+"${TEXFILE}.dvi: ${TEXFILE}.tex ${STYLEFILE}.sty\n\t${LATEX} ${TEXFILE} && ${LATEX} ${TEXFILE}\n"
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
    for i in self.projectdata.get_pages_with_boxdata():
      r=r+"\n% page"+str(i+1)+"\n"
      r=r+r'\begin{'
      r=r+self.pagename_frontend(i)
      r=r+r'}'
      r=r+"\n"
      for boxdata in self.projectdata.x_boxdata_in_the_page(i):
        if boxdata.type!=BoxData.TYPE_ENVIRONMENT and self.projectdata.table_contains(boxdata):
          r=r+"\n"+self.form_sample(boxdata,True)
        else:
          r=r+"\n"+self.form_sample(boxdata,False)
      r=r+"\n"
      for tabledata in self.projectdata.x_tabledata_in_the_page(i):
        r=r+"\n"+self.form_table_sample(tabledata)
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

  def dump_as_dictionary(self):
    d={}
    d["id"]=self.id
    d["page"]=self.page
    d["value"]=self.value
    d["is_horizontal"]=self.is_horizontal
    return d
  @classmethod
  def construct_from_dictionary(cls,d):
    return GridData(d["page"], d["value"],d["is_horizontal"],d["id"])

class TableData:
  serialnum=0
  def int2alphabet(self,n):
    r=""
    while n>19:
      r=chr(ord('a')+(n%20))+r
      n=(n-(n%20))//20
    return  chr(ord('a')+n)+r
  
  def __init__(self,table_of_id,id_as_int=None):
    if id_as_int==None:
      self.id_as_int=TableData.serialnum
      BoxData.serialnum=TableData.serialnum+1
    else:
      self.id_as_int=id_as_int
      BoxData.serialnum=max(TableData.serialnum,id_as_int)+1
    self.id=self.int2alphabet(self.id_as_int)
    self.table=[[rij for rij in ri] for ri in table_of_id]
    
  def dump_as_dictionary(self):
    d={}
    d["id_as_int"]=self.id_as_int
    d["table"]=self.table
    return d
  @classmethod
  def construct_from_dictionary(cls,d):
    r=TableData(d["table"],d["id_as_int"])
    return r

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
      r=chr(ord('a')+(n%20))+r
      n=(n-(n%20))//20
    return  chr(ord('a')+n)+r


  def __init__(self,page,x1,x2,y1,y2,id_as_int=None):
    if id_as_int==None:
      self.id_as_int=BoxData.serialnum
      BoxData.serialnum=BoxData.serialnum+1
    else:
      self.id_as_int=id_as_int
      BoxData.serialnum=max(BoxData.serialnum,id_as_int)+1
    self.id=self.int2alphabet(self.id_as_int)
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

  def dump_as_dictionary(self):
    d={}
    d["id_as_int"]=self.id_as_int
    d["x_1"]=self.x_1
    d["x_2"]=self.x_2
    d["y_1"]=self.y_1
    d["y_2"]=self.y_2
    d["name"]=self.name
    d["sampletext"]=self.sampletext
    d["page"]=self.page
    d["valign"]=self.valign
    d["halign"]=self.halign
    d["type"]=self.type
    return d
  @classmethod
  def construct_from_dictionary(cls,d):
    r=BoxData(d["page"],d["x_1"],d["x_2"],d["y_1"],d["y_2"],d["id_as_int"])
    r.name=d["name"]
    r.sampletext=d["sampletext"]
    r.valign=d["valign"]
    r.halign=d["halign"]
    r.type=d["type"]
    return r
  
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
    table.attach(sw,2,3,3,4)

    label=gtk.Label()
    label.set_markup("virtical align")
    table.attach(label,1,2,4,5)
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
    entry.set_value(boxdata.page)
    self.entry_page=entry
    table.attach(entry,2,3,7,8)

    label=gtk.Label()
    label.set_markup("top")
    table.attach(label,1,2,8,9)
    adjustment = gtk.Adjustment(value=boxdata.y_1,lower=0,upper=projectdata.lheight,step_incr=1,page_incr=1)
    entry=gtk.SpinButton(adjustment)
    entry.set_value(boxdata.y_1)
    self.entry_y1=entry
    table.attach(entry,2,3,8,9)
    
    label=gtk.Label()
    label.set_markup("bottom")
    table.attach(label,1,2,9,10)
    adjustment = gtk.Adjustment(value=boxdata.y_2,lower=0,upper=projectdata.lheight,step_incr=1,page_incr=1)
    entry=gtk.SpinButton(adjustment)
    entry.set_value(boxdata.y_2)
    self.entry_y2=entry
    table.attach(entry,2,3,9,10)

    label=gtk.Label()
    label.set_markup("left")
    table.attach(label,1,2,10,11)
    adjustment = gtk.Adjustment(value=boxdata.x_1,lower=0,upper=projectdata.lwidth,step_incr=1,page_incr=1)

    entry=gtk.SpinButton(adjustment)
    entry.set_value(boxdata.x_1)
    self.entry_x1=entry
    table.attach(entry,2,3,10,11)

    label=gtk.Label()
    label.set_markup("right")
    table.attach(label,1,2,11,12)
    adjustment = gtk.Adjustment(value=boxdata.x_2,lower=0,upper=projectdata.lwidth,step_incr=1,page_incr=1)
    entry=gtk.SpinButton(adjustment)
    entry.set_value(boxdata.x_2)
    self.entry_x2=entry
    table.attach(entry,2,3,11,12)

    self.set_editable_all(True)

    vbox.show_all()

  def get_box(self):
    return self.vbox

  def set_editable_all(self,is_editable):
    self.entry_name.set_editable(is_editable)
    self.entry_sampletext.set_editable(is_editable)
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
    self.boxdata.x_1=get_int_from_spinbutton(self.entry_x1)
    self.boxdata.x_2=get_int_from_spinbutton(self.entry_x2)
    self.boxdata.y_1=get_int_from_spinbutton(self.entry_y1)
    self.boxdata.y_2=get_int_from_spinbutton(self.entry_y2)

    return self.boxdata

class TableDataEntryArea:
  COMBO_VALIGN=[("top",BoxData.VALIGN_TOP),("center",BoxData.VALIGN_CENTER),("bottom",BoxData.VALIGN_BOTTOM)]
  COMBO_HALIGN=[("left",BoxData.HALIGN_LEFT),("center",BoxData.HALIGN_CENTER),("right",BoxData.HALIGN_RIGHT)]
  COMBO_TYPE=[("environment",BoxData.TYPE_ENVIRONMENT),("command",BoxData.TYPE_COMMAND),("checkmark",BoxData.TYPE_CHECKMARK),("strike",BoxData.TYPE_STRIKE),("rule",BoxData.TYPE_RULE),("check by circle",BoxData.TYPE_CHECK_CIRCLE)]

  def __init__(self,message,projectdata,current_page):
    self.projectdata=projectdata
    vbox=gtk.VBox()
    self.vbox=vbox
    label=gtk.Label()
    label.set_markup(message)
    vbox.pack_start(label,False,False,10)
    table=gtk.Table(2,10)
    vbox.add(table)

    label=gtk.Label()
    label.set_markup("virtical align")
    table.attach(label,1,2,4,5)
    combobox = gtk.combo_box_new_text()
    for i,(text,v) in enumerate(self.COMBO_VALIGN):
      combobox.append_text(text)
      #if boxdata.valign==v:
      #  combobox.set_active(i)
    combobox.set_active(1)
    self.entry_valign=combobox
    table.attach(combobox,2,3,4,5)

    label=gtk.Label()
    label.set_markup("horizontal align")
    table.attach(label,1,2,5,6)
    combobox = gtk.combo_box_new_text()
    for i,(text,v) in enumerate(self.COMBO_HALIGN):
      combobox.append_text(text)
      #if boxdata.halign==v:
      #  combobox.set_active(i)
    combobox.set_active(1)
    self.entry_halign=combobox
    table.attach(combobox,2,3,5,6)

    label=gtk.Label()
    label.set_markup("type")
    table.attach(label,1,2,6,7)
    combobox = gtk.combo_box_new_text()
    for i,(text,v) in enumerate(self.COMBO_TYPE):
      combobox.append_text(text)
      #if boxdata.type==v:
      #  combobox.set_active(i)
    combobox.set_active(1)
    self.entry_type=combobox
    table.attach(combobox,2,3,6,7)

    label=gtk.Label()
    label.set_markup("page")
    table.attach(label,1,2,7,8)
    adjustment = gtk.Adjustment(value=current_page,lower=0,upper=projectdata.n_pages,step_incr=1)
    entry=gtk.SpinButton(adjustment)
    entry.set_value(current_page)
    self.entry_page=entry
    table.attach(entry,2,3,7,8)

    label=gtk.Label()
    label.set_markup("t,b;t,b;...;t,b")
    table.attach(label,1,2,8,9)
    entry=gtk.Entry()
    self.entry_yy=entry
    entry.set_text("")
    table.attach(entry,2,3,8,9)

    label=gtk.Label()
    label.set_markup("l,r;l,r;...;l,r")
    table.attach(label,1,2,9,10)
    entry=gtk.Entry()
    entry.set_text("")
    self.entry_xx=entry
    table.attach(entry,2,3,9,10)

    self.set_editable_all(True)

    vbox.show_all()

  def get_box(self):
    return self.vbox

  def set_editable_all(self,is_editable):
    self.entry_page.set_editable(is_editable)
    self.entry_xx.set_editable(is_editable)
    self.entry_yy.set_editable(is_editable)

  def get_tabledata(self):
    valign=self.COMBO_VALIGN[self.entry_valign.get_active()][1]
    halign=self.COMBO_HALIGN[self.entry_halign.get_active()][1]
    boxtype=self.COMBO_TYPE[self.entry_type.get_active()][1]
    hilight=False
    page=get_int_from_spinbutton(self.entry_page)
    
    xx=self.get_grids(self.entry_xx.get_text())
    yy=self.get_grids(self.entry_yy.get_text())
    rr=[[BoxData(page,x1,x2,y1,y2) for (x1,x2) in xx]  for (y1,y2) in yy ]
    for ri in rr:
      for bi in ri:
        bi.valign=valign
        bi.halign=halign
        bi.type=boxtype
        bi.hilight=hilight
    rt=TableData([[ rij.id for rij in ri] for ri in rr])
    return (rr,rt)

  def get_grids(self,s):
    rr=[ si.split(",") for si in s.split(";")]    
    return [(int(ri[0]),int(ri[-1])) for ri in rr]
  
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
    
    tvcolumn = gtk.TreeViewColumn('y')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 6)
    treeview.set_reorderable(True)


    tvcolumn = gtk.TreeViewColumn("y'")
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 7)
    treeview.set_reorderable(True)
    
    tvcolumn = gtk.TreeViewColumn('x')
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 4)
    treeview.set_reorderable(True)

    tvcolumn = gtk.TreeViewColumn("x'")
    treeview.append_column(tvcolumn)
    cell = gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 5)
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
    self.buttonbox=hbox
    
    button = gtk.Button(stock=gtk.STOCK_NEW)
    hbox.add(button)
    self.button_new=button
    button = gtk.Button(stock=gtk.STOCK_REMOVE)
    hbox.add(button)
    self.button_remove=button
    button = gtk.Button(stock=gtk.STOCK_EDIT)
    hbox.add(button)
    self.button_edit=button

    vbox.show_all()
    for boxdata in self.parent.projectdata.boxes:
      self.append_boxdata(boxdata)
  def get_vbox(self):
    return self.vbox
  
  def get_buttonbox(self):
    return self.buttonbox
  
  def get_buttons(self):
    return (self.button_new,self.button_remove,self.button_edit)

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
    for box in self.projectdata.x_boxdata_in_the_page(self.page):
      (x1,x2,width,y1,y2,height)=self.projectdata.get_box_coordinate(box)
      
      (r,g,b,a)=(0.3, 0.3, 0.6,1.0)
      ctx.set_source_rgba(r,g,b,a)
      ctx.select_font_face('Serif', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
      ctx.set_font_size(12)
      ctx.move_to(x1, y2)
      ctx.show_text(box.id)
      
      if box.hilight:
        (r,g,b,a)=(0.9,0.2,0.4, 0.005)
      else:
        (r,g,b,a)=(1,0.5,0.5, 0.1)
      ctx.set_source_rgba(r,g,b,a)

      ctx.new_path()
      if box.valign==BoxData.VALIGN_TOP:
        if box.halign==BoxData.HALIGN_LEFT:
          a=0.8
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y1)                      
          ctx.line_to(x1, (y1+y2)/2)
          ctx.stroke()
          a=0.3
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y1)                      
          ctx.line_to(x1, (y1+y2)/2)
          ctx.line_to(x1, y1)
          ctx.close_path()                       
          ctx.fill()

        elif box.halign==BoxData.HALIGN_RIGHT:
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y1)                      
          ctx.line_to(x2, (y1+y2)/2)
          ctx.stroke()
          a=0.3          
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y1)                      
          ctx.line_to(x2, (y1+y2)/2)
          ctx.line_to(x2, y1)
          ctx.close_path()                       
          ctx.fill()
        else:
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x1,y1)
          ctx.line_to((x1+x2)/2,(y1+y2)/2)
          ctx.line_to(x2,y1)
          ctx.stroke()
          a=0.3
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x1,y1)
          ctx.line_to((x1+x2)/2,(y1+y2)/2)
          ctx.line_to(x2,y1)
          ctx.close_path()                       
          ctx.fill()
      elif box.valign==BoxData.VALIGN_BOTTOM:
        if box.halign==BoxData.HALIGN_LEFT:
          a=0.8
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y2)                      
          ctx.line_to(x1, (y1+y2)/2)
          ctx.stroke()

          a=0.3
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y2)                      
          ctx.line_to(x1, (y1+y2)/2)
          ctx.line_to(x1, y2)
          ctx.close_path()                       
          ctx.fill()

        elif box.halign==BoxData.HALIGN_RIGHT:
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y2)                      
          ctx.line_to(x2, (y1+y2)/2)
          ctx.stroke()

          a=0.3
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y2)                      
          ctx.line_to(x2, (y1+y2)/2)
          ctx.line_to(x2, y2)
          ctx.close_path()                       
          ctx.fill()
        else:
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x1,y2)
          ctx.line_to((x1+x2)/2,(y1+y2)/2)
          ctx.line_to(x2,y2)
          ctx.stroke()
          a=0.3
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x1,y2)
          ctx.line_to((x1+x2)/2,(y1+y2)/2)
          ctx.line_to(x2,y2)
          ctx.close_path()                       
          ctx.fill()
      else:
        if box.halign==BoxData.HALIGN_LEFT:
          a=0.8
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x1,y1)
          ctx.line_to((x1+x2)/2, (y1+y2)/2)
          ctx.line_to(x1,y2)
          ctx.stroke()
          a=0.3
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x1,y1)
          ctx.line_to((x1+x2)/2, (y1+y2)/2)
          ctx.line_to(x1,y2)
          ctx.close_path()                       
          ctx.fill()
          
        elif box.halign==BoxData.HALIGN_RIGHT:
          a=0.8
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x2,y1)
          ctx.line_to((x1+x2)/2, (y1+y2)/2)
          ctx.line_to(x2,y2)
          ctx.stroke()
          a=0.3
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x2,y1)
          ctx.line_to((x1+x2)/2, (y1+y2)/2)
          ctx.line_to(x2,y2)
          ctx.close_path()                       
          ctx.fill()

        else:
          a=0.8
          ctx.set_source_rgba(r,g,b,a)
          ctx.new_path()
          ctx.move_to(x1+0.4*width,(y1+y2)/2)
          ctx.line_to(x2-0.4*width,(y1+y2)/2)
          ctx.stroke()
          ctx.new_path()
          ctx.move_to((x1+x2)/2,y1+0.35*height)
          ctx.line_to((x1+x2)/2,y2-0.35*height)
          ctx.stroke()


      a=0.1
      ctx.set_source_rgba(r,g,b,a)
      ctx.new_path()
      ctx.move_to(x1, y1)                      
      ctx.rel_line_to(width, 0)       
      ctx.rel_line_to(0, height)      
      ctx.rel_line_to(-width, 0)  
      ctx.close_path()                       
      ctx.fill()

      a=0.8
      ctx.set_source_rgba(r,g,b,a)
      ctx.set_line_width(0.5)
      ctx.new_path()                         
      ctx.move_to(x1, y1)                      
      ctx.rel_line_to(width, 0)       
      ctx.rel_line_to(0, height)      
      ctx.rel_line_to(-width, 0)  
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
      dy=int(height/6)



class Bar(gtk.DrawingArea):
  def __init__(self,direction,margin):
    gtk.DrawingArea.__init__(self)
    self.width = self.height = 0
    self.direction=direction
    self.connect('size-allocate', self.on_self_size_allocate)
    self.connect('expose-event', self.on_self_expose_event)
    self.margin=margin
    self.hilight_mode=0
    self.hilight_spot_size=8

  def set_hilight_mode(self,mode):
    self.hilight_mode=mode
    
  def get_background_rgba(self):
    if self.hilight_mode==0:
      return (0.1,0.2,1.0,1)
    elif self.hilight_mode==1:
      return (0.3,0.7,0.7,1)
    elif self.hilight_mode==2:
      return (0.5,0.1,0.1,1)
    elif self.hilight_mode==3:
      return (0.1,0.5,0.5,1)
    elif self.hilight_mode==4:
      return (0.1,0.5,0.1,1)
    elif self.hilight_mode==5:
      return (1.0,1.0,0.5,1)
    else:
      return (0.5,0.5,0.5,0.5)
    
  def get_line_rgba(self):
    if self.hilight_mode==0:
      return (0.4,0.05,0.05,0.5)
    elif self.hilight_mode==1:
      return (1.0,0.3,0.3,0.5)
    elif self.hilight_mode==2:
      return (0.1,0.1,0.5,0.5)
    elif self.hilight_mode==3:
      return (0.1,0.5,0.5,0.5)
    elif self.hilight_mode==4:
      return (0.5,0.1,0.5,0.5)
    elif self.hilight_mode==5:
      return (0.5,0.5,0.1,0.5)
    else:
      return (0.5,0.5,0.5,0.5)


  def on_self_size_allocate(self, widget, allocation):
    self.width = allocation.width
    self.height = allocation.height
    
  def on_self_expose_event(self, widget, event):
    ctx = widget.window.cairo_create()

    if self.direction & BarOnLayout.MASK_VIRTICAL_BAR:
      c = self.get_line_rgba()
      if c != None:
        (r,g,b,a)=c
        ctx.set_source_rgba(r,g,b,a)
        ctx.new_path()
        ctx.move_to(0, 0)
        ctx.rel_line_to(0,self.height)
        ctx.rel_line_to(1, 0)
        ctx.rel_line_to(0,-self.height)
        ctx.close_path()
        ctx.fill()
      c = self.get_background_rgba()
      if c != None:
        (r,g,b,a)=c
        ctx.set_source_rgba(r,g,b,a)
        ctx.new_path()                         
        ctx.move_to(0, self.margin)
        ctx.rel_line_to(0,self.hilight_spot_size)      
        ctx.rel_line_to(self.width, 0)       
        ctx.rel_line_to(0,-self.hilight_spot_size)      
        ctx.close_path()                       
        ctx.fill() 

    else:
      c= self.get_line_rgba()
      if c!=None:
        (r,g,b,a)=c
        ctx.set_source_rgba(r,g,b,a)
        ctx.new_path()                         
        ctx.move_to(0, self.height)                      
        ctx.rel_line_to(self.width, 0)       
        ctx.rel_line_to(0,-1)      
        ctx.rel_line_to(-self.width, 0)  
        ctx.close_path()                       
        ctx.fill() 
      c= self.get_background_rgba()
      if c!=None:
        (r,g,b,a)=c
        ctx.set_source_rgba(r,g,b,a)
        ctx.new_path()                         
        ctx.move_to(self.margin, 0)                      
        ctx.rel_line_to(self.hilight_spot_size, 0)       
        ctx.rel_line_to(0,self.height)      
        ctx.rel_line_to(-self.hilight_spot_size, 0)  
        ctx.close_path()                       
        ctx.fill() 

class SpinButtonForBarOnLayout(gtk.SpinButton):
  def __init__(self,adj_max,a,b,id_adj,id_spb):
    adj=gtk.Adjustment(value=0,lower=0,upper=adj_max, step_incr=-1)
    gtk.SpinButton.__init__(self,adj,a,b)
    self.set_width_chars(5)
    self.set_alignment(1.0)
    self.bars=[]
    self.current_bar=None
    self.id_adj=id_adj
    self.id_spb=id_spb
    self.update_upper_and_lower()


  def append_bar(self,bar):
    self.bars.append(bar)
    self.update_upper_and_lower()

  def update_upper_and_lower(self):
    if self.bars==[]:
      self.id_adj.set_upper(-1)
      self.id_adj.set_lower(1)
    else:
      m=max([bar.griddata.id for bar in self.bars])
      self.id_adj.set_upper(m)
      m=min([bar.griddata.id for bar in self.bars])
      self.id_adj.set_lower(m)
    
  def set_current_bar(self,bar):
    if self.current_bar != None:
      self.current_bar.set_hilight_mode(0)
    if bar != None:
      bar.set_hilight_mode(1)
    if bar != self.current_bar:
      self.current_bar=bar
    if bar != None:
      self.set_value(bar.get_value())
    else:
      self.set_value(0)
    if self.current_bar.griddata.id != get_int_from_spinbutton(self.id_spb):
      self.id_spb.set_value(self.current_bar.griddata.id)
      
  def get_bar_by_id(self,bar_id):
    for bar in self.bars:
      if bar.griddata.id==bar_id:
        return bar
    return None
  
  def set_current_bar_on_changed(self,widget):
    bar_id=get_int_from_spinbutton(widget)
    bar=self.get_bar_by_id(bar_id)
    self.set_current_bar(bar)

  def move_bar_on_changed(self,widget):
    if self.current_bar != None:
      self.current_bar.set_value(get_int_from_spinbutton(self))

class BarOnLayout(gtk.EventBox):
  MASK_VIRTICAL_BAR=2
  MASK_OPPOSIT_DIRECTION=1
  LINEWIDTH=1
  def __init__(self,direction,max_x,max_y,spinbuttonforbar,griddata,current_page):
    gtk.EventBox.__init__(self)
    self.x=0
    self.y=0
    self.direction=direction
    self.max_x=max_x
    self.max_y=max_y
    self.griddata=griddata
    self.spinbutton=spinbuttonforbar
    
    if direction & self.MASK_VIRTICAL_BAR:
      self.height=max_y
      self.width=self.LINEWIDTH
      self.margin=(13+9*griddata.id)%self.height
      box=gtk.HBox()
      label_box=gtk.VBox()
      label_box.pack_start(gtk.HSeparator(),False,False,0)
    else:
      self.width=max_x
      self.height=self.LINEWIDTH
      self.margin=(13+4*griddata.id)%self.width
      box=gtk.VBox()
      label_box=gtk.HBox()
      label_box.pack_start(gtk.VSeparator(),False,False,0)

    drawingarea = Bar(direction,self.margin)
    self.drawingarea=drawingarea
    drawingarea.set_size_request(self.width,self.height)
    self.set_visible(True)
    self.set_visible_window(False)

    self.add(box)
    box.add(drawingarea)
    label=gtk.Label()
    label.set_markup('<span foreground="#0055FF" size="small">'+str(self.griddata.id)+'</span>')
    label_box.pack_start(label,False, False, 0)
    box.add(label_box)
    label_box.show_all()
    label.show()
    box.show()
    self.label_box=label_box
    

    drawingarea.show()
    self.draging=False
    self.connect("motion_notify_event", self.motion_notify_event)
    self.connect("button_press_event", self.button_press_event)
    self.connect("button_release_event", self.button_release_event)
    self.current_page=current_page
    self.hilight_mode=0
    self.should_hide_if_not_current_page=True
    self.should_hide_whenever=False
    self.set_hilight()
    self.spinbutton.append_bar(self)


  def set_hilight(self):
    if self.current_page==self.griddata.page:
      self.set_visible(not self.should_hide_whenever)
      if self.hilight_mode==0:
        self.drawingarea.set_hilight_mode(0)
      else:
        self.drawingarea.set_hilight_mode(1)
    else:
      if self.hilight_mode==0:
        self.set_visible(not self.should_hide_if_not_current_page and not self.should_hide_whenever)
        self.drawingarea.set_hilight_mode(2)
      else:
        self.set_visible(not self.should_hide_whenever)
        self.drawingarea.set_hilight_mode(3)
        
  def set_hilight_mode(self,mode):
    self.hilight_mode=mode
    self.set_hilight()
    
  def set_current_page(self,p,should_hide_if_not_current_page,should_hide_whenever):
    self.current_page=p
    self.should_hide_if_not_current_page=should_hide_if_not_current_page
    self.should_hide_whenever=should_hide_whenever
    self.set_hilight()

  def get_spinbutton(self):
    return self.spinbutton
  
  def get_value(self):
    return self.griddata.value

  def set_value(self,v):
    if self.draging:
      return
    if self.direction & self.MASK_VIRTICAL_BAR:
      if v<0:
        v=0
      if self.max_x<v:
        v=self.max_x
      self.griddata.value=int(v)
      self.move_horizontal(self.griddata.value)
      self.parent.refresh_preview()
    else:
      if v<0:
        v=0
      if self.max_y<v:
        v=self.max_y
      self.griddata.value=int(v)
      self.move_virtical(v)
      self.parent.refresh_preview()


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
    else:
      self.griddata.value=self.x

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
    self.label_box.set_spacing(y*4 % 60)
    self.drawingarea.margin=y*4 % 60
    self.drawingarea.hilight_spot_size=16
      
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
    self.label_box.set_spacing(x*5 % 75)
    self.drawingarea.margin=x*5 % 75
    self.drawingarea.hilight_spot_size=20

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
    self.draging=False
    if self.direction & self.MASK_VIRTICAL_BAR:
      self.set_value(x-self.margin_x)
    else:
      self.set_value(y-self.margin_y)
    self.margin_x = 0
    self.margin_y = 0
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

class TableDataDialog(gtk.Dialog):
  def __init__(self,title=None, parent=None, flags=0, buttons=None,message="",projectdata=None,current_page=0):
    gtk.Dialog.__init__(self,title,parent,flags,buttons)
    self.area=TableDataEntryArea(message,projectdata,current_page)
    self.vbox.pack_start(self.area.get_box())

  def get_tabledata(self):
    return self.area.get_tabledata()

class HoganDialog(gtk.Dialog):
  def __init__(self,title=None, parent=None, flags=0, buttons=None, projectdata=None,p=0):
    gtk.Dialog.__init__(self,title,parent,flags,buttons)
    self.area=LayoutOverBoxesWithHoganArea(projectdata,p)
    self.vbox.pack_start(self.area.get_box())
    (w,h)=projectdata.get_default_dialog_size()
    self.resize(w,h)

  def get_currentpage(self):
    return self.area.get_currentpage()

  def refresh_preview(self):
    if self.area:
      self.area.refresh_preview()


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

    self.coordinate_hbox.add(gtk.VSeparator())

    hbox=gtk.HBox()
    coordinate_hbox.add(hbox)
    label=gtk.Label()
    hbox.add(label)
    label.set_markup("Current page: ")
    
    adj = gtk.Adjustment(value=p, lower=0,upper=self.projectdata.n_pages-1, step_incr=-1)
    entry=gtk.SpinButton(adj, 0, 0)
    entry.connect("changed", self.on_page_changed_event)
    hbox.add(entry)

    
    self.coordinate_hbox.add(gtk.VSeparator())

    hbox=gtk.HBox()
    self.coordinate_hbox.add(hbox)
    label=gtk.Label()
    hbox.add(label)
    label.set_markup("Forcused grid: ")
    adj = gtk.Adjustment(value=p, lower=0,upper=-1, step_incr=-1)
    entry=gtk.SpinButton(adj, 0, 0)
    hbox.add(entry)

    hbox=gtk.HBox()
    self.coordinate_hbox.add(hbox)
    label=gtk.Label()
    hbox.add(label)
    label.set_markup("Value: ")
    w=self.projectdata.lwidth
    h=self.projectdata.lheight
    self.spb=SpinButtonForBarOnLayout(max(w,h),0,0,adj,entry)
    hbox.add(self.spb)
    self.spb.connect("changed", self.spb.move_bar_on_changed)
    entry.connect("changed", self.spb.set_current_bar_on_changed)

    
    self.coordinate_hbox.add(gtk.VSeparator())
  
    hbox = gtk.HButtonBox()
    coordinate_hbox.add(hbox)
    hbox.set_layout(gtk.BUTTONBOX_CENTER)
    
    combobox = gtk.combo_box_new_text()
    hbox.add(combobox)
    combobox.append_text("---")
    combobox.append_text(" | ")
    combobox.connect('changed', self.toggle_ruler_direction_onchange)
    self.new_ruler_will_be_horizontal=True
    combobox.set_active(0)
    
    button = gtk.Button(stock=gtk.STOCK_ADD)
    hbox.add(button)
    self.button_edit=button
    button.connect('clicked', self.add_new_ruler_onclick)


    self.coordinate_hbox.add(gtk.VSeparator())

    checkbutton= gtk.CheckButton("hide all")
    checkbutton.show()
    checkbutton.connect("toggled", self.on_toggle_hide_grid)
    self.coordinate_hbox.add(checkbutton)

    self.coordinate_hbox.add(gtk.VSeparator())


    self.rulers=[]

    coordinate_hbox.show_all()
    box.pack_start(coordinate_hbox, False, False, 0)

    hbox=gtk.HBox()
    hbox.add(box)
    hbox.show_all()
    self.box=hbox
        
    self.current_page=self.layout.page
    self.should_hide_if_not_current_page=True
    self.should_hide_whenever=False

    for griddata in self.projectdata.grids:
      self.add_ruler(griddata)
      
  def add_ruler(self,griddata):
    w=self.projectdata.lwidth
    h=self.projectdata.lheight
    p=self.layout.page
    if griddata.is_horizontal:
      bar=BarOnLayout(1,w,h,self.spb,griddata,p)
    else:
      bar=BarOnLayout(2,w,h,self.spb,griddata,p)
    self.rulers.append(bar)
    bar.show()
    self.layout.add(bar)
    bar.set_value(griddata.value)

  def add_new_ruler(self):
    if self.new_ruler_will_be_horizontal:
      v=self.projectdata.lheight
    else:
      v=self.projectdata.lwidth
    p=self.layout.page
    g=GridData(p,v//2,self.new_ruler_will_be_horizontal)
    self.add_ruler(g)
    self.projectdata.add_grid(g)
    
  def add_new_ruler_onclick(self,widget):
    self.add_new_ruler()
  
  def toggle_ruler_direction_onchange(self,widget):
    if widget.get_active()==0:
      self.new_ruler_will_be_horizontal=True
    elif widget.get_active()==1:
      self.new_ruler_will_be_horizontal=False

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
    p=get_int_from_spinbutton(widget)
    self.current_page=p
    self.update_rulers()
    self.layout.set_page(p)

  def on_toggle_hide_grid(self, widget):
    if widget.get_active()==0:
      self.should_hide_whenever=False
    else:
      self.should_hide_whenever=True
    self.update_rulers()
    self.should_hide_whenever
      
  def update_rulers(self):
    for ri in self.rulers:
      ri.set_current_page(self.current_page,self.should_hide_if_not_current_page,self.should_hide_whenever)

  def get_currentpage(self):
    return self.layout.page

class ProjectData:
  HEIGHT = 600
  WIDTH = 600
  DEFAULT_SAMPLE_BASE="sample"
  DEFAULT_JSON_BASE="projectdata"
  DEFAULT_JSON_EXT=".json"
  DEFAULT_MAKEFILE_PATH="Makefile"

  def __init__(self,uri):
    p=urlparse.urlparse(uri)
    path=urllib.unquote(p.path)
    (self.destdir,filename)=os.path.split(path)
    (base,ext)=os.path.splitext(filename)
    
    if ext==self.DEFAULT_JSON_EXT:
      f = open(path)
      prev_proj= json.load(f)
      self.bgimagepath=prev_proj["bgimagepath"]
      self.bgimagefullpath=os.path.join(self.destdir,self.bgimagepath)
      prev_proj["pdfuri"]='file://'+urllib.pathname2url(self.bgimagefullpath)
      self.destdir=os.path.join(self.destdir,"..")
    else:
      self.bgimagefullpath=path
      self.bgimagepath=filename
      prev_proj={}
      prev_proj["pdfuri"]=uri
    self.set_document(prev_proj["pdfuri"])
    
    if "stylename" in prev_proj:
      self.stylename=prev_proj["stylename"]
    else:
      self.stylename=base
    if "samplebase" in prev_proj:
      self.samplebase=prev_proj["samplebase"]
    else:
      self.samplebase=self.DEFAULT_SAMPLE_BASE
    if "makefilepath" in prev_proj:
      self.makefilepath=prev_proj["makefilepath"]
    else:
      self.makefilepath=self.DEFAULT_MAKEFILE_PATH
    if "jsonpath" in prev_proj:
      self.jsonpath=prev_proj["jsonpath"]
    else:
      self.jsonpath=self.DEFAULT_JSON_BASE+self.DEFAULT_JSON_EXT

    self.samplepath=self.samplebase+".tex"  

    if "boxes" in prev_proj:
      self.boxes=[BoxData.construct_from_dictionary(d) for d in prev_proj["boxes"]]
    else:
      self.boxes=[]
    if "grids" in prev_proj:
      self.grids=[GridData.construct_from_dictionary(d) for d in prev_proj["grids"]]
    else:
      self.grids=[]
    if "tables" in prev_proj:
      self.tables=[TableData.construct_from_dictionary(d) for d in prev_proj["tables"]]
    else:
      self.tables=[]
    

  def set_document(self,uri):    
    self.boundingboxes=[]
    if uri:
      self.document = poppler.document_new_from_file(uri,None)
    else:
      self.document=None
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
    self.set_default_dialog_size((self.lwidth,self.lheight))

    
  def get_pages_with_boxdata(self):
    pages=list(set([boxdata.page for boxdata in self.boxes]))
    pages.sort()
    return pages

  def x_boxdata_in_the_page(self,i):
    for boxdata in self.boxes:
      if boxdata.page==i:
        yield boxdata
  def x_tabledata_in_the_page(self,i):
    for tabledata in self.tables:
      boxdata=self.get_boxdata_by_id(tabledata.table[0][0])
      if boxdata.page==i:
        yield tabledata
  def table_contains(self,boxdata):
    for tabledata in self.tables:
      for ri in tabledata.table:
        for rij in ri:
          if rij==boxdata.id:
            return True
    return False

  def add_boxdata(self,boxdata):
    self.boxes.append(boxdata)

  def add_tabledata(self,tabledata):
    self.tables.append(tabledata)

  def add_grid(self,grid_data):
    self.grids.append(grid_data)

  def get_griddata_by_id(self,id):
    for griddata in self.grids:
      if griddata.id==id:
        return griddata
    return None

  def get_grid_coordinate_by_id(self,id):
    g=self.get_griddata_by_id(id)
    if g==None:
      return 0    
    return g.value

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

                                     
  def get_box_coordinate(self,box):
    a=self.get_grid_coordinate_by_id(box.x_1)
    b=self.get_grid_coordinate_by_id(box.x_2)
    x1=min(a,b)
    x2=max(a,b)
    width=x2-x1
    a=self.get_grid_coordinate_by_id(box.y_1)
    b=self.get_grid_coordinate_by_id(box.y_2)
    y1=min(a,b)
    y2=max(a,b)
    height=y2-y1
    return (x1,x2,width,y1,y2,height)
  
  def get_page(self,page):
    if self.pages[page]:
      return self.pages[page]
    else:
      self.pages[page]=self.document.get_page(page)
      return self.pages[page]

  def output_to_zipfile(self,destzip,rootdir):
    print "writing imagefiles...."
    afd=applicationFormData(self)
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
    makefilepath=os.path.join(rootdir,self.makefilepath)
    inf=zipfile.ZipInfo(makefilepath)
    destzip.writestr(inf,afd.get_sample_makefile(self.samplebase,self.stylename))

    print "writing this project data...."
    jsonfilepath=os.path.join(rootdir,self.jsonpath)
    inf=zipfile.ZipInfo(jsonfilepath)
    destzip.writestr(inf,self.dump_as_json())
    
    for inf in destzip.infolist():
      inf.external_attr = 0755 << 16L
      inf.create_system = 0
    destzip.close()
    print "done."

  def get_default_dialog_size(self):
    return self.dialogsize
  
  def set_default_dialog_size(self,s):
    self.dialogsize=s

  def dump_as_dictionary(self):
    d={}
    d["bgimagepath"]=self.bgimagepath
    d["stylename"]=self.stylename
    d["samplebase"]=self.samplebase
    d["makefilepath"]=self.makefilepath
    d["jsonpath"]=self.jsonpath
    d["boxes"]=[box.dump_as_dictionary() for box in self.boxes]
    d["grids"]=[grid.dump_as_dictionary() for grid in self.grids]
    d["tables"]=[table.dump_as_dictionary() for table in self.tables]
    return d
  
  def dump_as_json(self):
    d=self.dump_as_dictionary()
    return json.dumps(d,indent=2)
    
class AFMMainArea:
  def __init__(self,projectdata):
    self.projectdata=projectdata
    self.preview=None    
    self.box=gtk.VBox()
    listarea=BoxDataListArea(self)
    self.box.pack_start(listarea.get_vbox())
    self.listarea=listarea
    (button_new,button_remove,button_edit)=listarea.get_buttons()
    button_new.connect('clicked', self.on_click_new)
    button_remove.connect('clicked', self.on_click_remove)
    button_edit.connect('clicked', self.on_click_edit)

    hbbox = gtk.HButtonBox()
    listarea.get_buttonbox().pack_start(hbbox,expand=False, fill=False)

    hbbox.set_layout(gtk.BUTTONBOX_END)
    button = gtk.Button("Add a table")
    button.connect('clicked', self.on_click_addtable)
    hbbox.add(button)


    hbbox = gtk.HButtonBox() 
    listarea.get_vbox().pack_start(hbbox,expand=False, fill=False)
    hbbox.set_layout(gtk.BUTTONBOX_END)

    hbbox.set_layout(gtk.BUTTONBOX_END)
    button = gtk.Button("Show Grids/Preview")
    button.connect('clicked', self.on_click_preview)
    hbbox.add(button)
    self.open_preview_button=button
    
    button = gtk.Button(stock=gtk.STOCK_SAVE_AS)
    button.connect('clicked', self.on_click_save_as)
    hbbox.add(button)
    hbbox.show_all()

    self.box.show_all()


    
  def open_preview_dialog(self):
    dialog=HoganDialog("Preview",None,
                       gtk.DIALOG_DESTROY_WITH_PARENT,
                       None,
                       self.projectdata,0)
    dialog.connect("delete_event", self.on_delete_preview_dialog)
    dialog.show()
    self.preview=dialog
  
  def on_delete_preview_dialog(self,widget,event,data=None):
    self.preview=None
    self.open_preview_button.set_sensitive(True)
    return False
  

  def get_box(self):
    return self.box

  def on_click_preview(self,widget):
    self.open_preview_button.set_sensitive(False)
    if self.preview == None:
      self.open_preview_dialog()

  
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
    #gtk.main_quit()

  def refresh_preview(self):
      if self.preview:
        self.preview.refresh_preview()
        
  def get_initial_boxdata(self):
    p=0
    x1=0
    x2=1
    y1=2
    y2=3
    if self.preview != None:
      p=self.preview.get_currentpage()

    xx=[(griddata.value,griddata.id) for griddata in self.projectdata.grids if not griddata.is_horizontal  if griddata.page==p]
    if len(xx)>0:
      xx.sort()
      x1=xx[0][1]
      x2=xx[-1][1]
    else:
      xx=[(griddata.value,griddata.id) for griddata in self.projectdata.grids if not griddata.is_horizontal]
      if len(xx)>0:
        xx.sort()
        x1=xx[0][1]
        x2=xx[-1][1]
    yy=[(griddata.value,griddata.id) for griddata in self.projectdata.grids if  griddata.is_horizontal and griddata.page==p]
    if len(yy)>0:
      yy.sort()
      y1=yy[0][1]
      y2=yy[-1][1]
    else:
      yy=[(griddata.value,griddata.id) for griddata in self.projectdata.grids if griddata.is_horizontal]
      if len(yy)>0:
        yy.sort()
        y1=yy[0][1]
        y2=yy[-1][1]
    
    return BoxData(p,x1,x2,y1,y2)
  
  def on_click_addtable(self,widget):
    self.confirm_and_addtable()
    
  def confirm_and_addtable(self):
    title="New Table."
    message="Add boxes:"
    p=0
    if self.preview != None:
      p=self.preview.get_currentpage()
    t=self.get_tabledata_by_dialog(title,message,p)
    if t:
      (boxes,tabledata)=t
      for row in boxes:
        for boxdata in row:
          self.listarea.append_boxdata(boxdata)
          self.projectdata.add_boxdata(boxdata)
      self.projectdata.add_tabledata(tabledata)
      self.refresh_preview()

  
  def on_click_new(self,widget):
    boxdata=self.get_initial_boxdata()
    self.confirm_and_add(boxdata)

  def confirm_and_add(self,boxdata):
    title="New box."
    message="Add the following box:"
    boxdata=self.get_valid_boxdata_by_dialog(boxdata,title,message)
    if boxdata:
      self.listarea.append_boxdata(boxdata)
      self.projectdata.add_boxdata(boxdata)
      self.refresh_preview()

  def on_click_remove(self,widget):
    (model,iteralist,boxids)=self.listarea.get_selected_ids()
    if not boxids:
      return
    for (itera,boxid,) in zip(iteralist,boxids):
      self.confirm_and_remove_by_id(boxid,model,itera)

  def confirm_and_remove_by_id(self,boxid,model,itera):
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

  def get_tabledata_by_dialog(self,title,message,current_page):
    mode=gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL
    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)                           
    dialog=TableDataDialog(title,None,mode,buttons,message,self.projectdata,current_page)
    r = dialog.run()
    if r==gtk.RESPONSE_ACCEPT:
      tabledata=dialog.get_tabledata()
    else:
      tabledata=None
    dialog.destroy()
    return tabledata

  def get_boxdata_by_dialog(self,boxdata,title,message):
    mode=gtk.DIALOG_DESTROY_WITH_PARENT|gtk.DIALOG_MODAL
    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
    dialog=BoxDataDialog(title,None,mode,buttons,boxdata,message,self.projectdata)

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
    layout = AFMMainArea(self.projectdata)
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
    dialog = gtk.FileChooserDialog('Choose pdf file.',
                                   None,
                                   buttons=(gtk.STOCK_CANCEL,
                                            gtk.RESPONSE_REJECT,
                                            gtk.STOCK_OPEN,
                                            gtk.RESPONSE_ACCEPT))
    filter = gtk.FileFilter()
    filter.set_name("PDF files")
    filter.add_mime_type("application/pdf")
    filter.add_mime_type("application/x-pdf")
    filter.add_pattern("*.pdf")
    dialog.add_filter(filter)
    filter = gtk.FileFilter()
    filter.set_name("project JSON files")
    filter.add_mime_type("application/json")
    filter.add_mime_type("application/x-json")
    filter.add_pattern("*"+ProjectData.DEFAULT_JSON_EXT)
    dialog.add_filter(filter)
    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    r = dialog.run()
    if r==gtk.RESPONSE_ACCEPT:
      uri=dialog.get_uri()
      dialog.destroy()
    else:
      dialog.destroy()

  if uri:
    Afmmain(uri)
    gtk.main()

