#!/usr/bin/env python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk 
from gi.repository import Gio 
from gi.repository import Gdk 
from gi.repository import GLib
from gi.repository import GdkPixbuf 
from gi.repository import Pango
from gi.repository import cairo

try:
  gi.require_version('Poppler', '0.18')
  from gi.repository import Poppler
  rendering_library_name='poppler'
except:
  #To use fitz, install pymupdf not fitz by pip
  ##pip3 install pymupdf
  try:
    import fitz
    import io
    rendering_library_name='mupdf'
  except:
    import pdf2image
    import pdfrw
    import io
    from gi.repository import GLib, GdkPixbuf
    rendering_library_name='pdf2image'
print("Loaded", rendering_library_name, "as pdf rendering library")
import sys
import zipfile
import os.path
import os
import urllib
import urllib.parse
import urllib.request
import json
import re
import string
import time


def print_log(comment):
  print("#Log:", comment)

def get_int_from_spinbutton(spinbutton):
  if spinbutton.get_text():
    return int(spinbutton.get_text())
  else:
    return spinbutton.get_value_as_int()

#####################################################
def get_pdfdocument_from_uri(uri):
  if rendering_library_name=='poppler':
    return pdfDocumentByPoppler(uri)
  elif rendering_library_name=='mupdf':
    return pdfDocumentByPymupdf(uri)
  elif rendering_library_name=='pdf2image':
    return pdfDocumentByPdf2image(uri)
  else:
    return None

class pdfRenderer:
  def get_n_pages(self):
    pass
  def get_size_of_page(self,i):
    pass
  def paint_page(self,page,ctx):
    pass

class pdfDocumentByPoppler(pdfRenderer):
  def __init__(self,uri):
    #self.document = Poppler.document_new_from_file(uri,None)
    self.document = Poppler.Document.new_from_file(uri,None)
    self.pages=[ None for i in range(self.get_n_pages())]
      
  def paint_page(self,page,ctx):
    self.get_page(page).render(ctx)

  def get_n_pages(self):
    return self.document.get_n_pages()

  def get_size_of_page(self,page):
    return self.get_page(page).get_size()
    
  def get_page(self,page):
    if self.pages[page]:
      return self.pages[page]
    else:
      self.pages[page]=self.get_page_img(page)
      return self.pages[page]

  def get_page_img(self,page):
    return self.document.get_page(page)

class pdfDocumentByPdf2image(pdfRenderer):
  def __init__(self,uri):
    #self.document = Poppler.document_new_from_file(uri,None)
    filename = uri[7:]
    pdf = pdfrw.PdfReader(filename)
    bb=pdf.pages[0].MediaBox
    size=(float(bb[2]),float(bb[3]))
    #self.pages = pdf2image.convert_from_path(uri,size=size,fmt="png")
    self.pages = pdf2image.convert_from_path(uri,size=size)
  def get_n_pages(self):
    return len(self.pages)

  def get_size_of_page(self,page):
    return self.pages[page].size

  def paint_page(self,page,ctx):
    img = self.image2pixbuf(self.pages[page])
    Gdk.cairo_set_source_pixbuf(ctx,img,0,0)
    ctx.paint()
    #img = self.image2imagesurface(self.pages[page])
    #ctx.set_source_surface(img,0,0)
    #ctx.paint()


  def image2pixbuf(self,im):
    data = im.tobytes()
    (w,h) = im.size
    data = GLib.Bytes.new(data)
    pix = GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB, False, 8, w, h, w * 3)
    return pix
  
  def image2imagesurface(self,img):
    return cairo.image_surface_create(img)
  


class pdfDocumentByPymupdf(pdfRenderer):
  def __init__(self,uri):
    p=urllib.parse.urlparse(uri)
    path=urllib.parse.unquote(p.path)
    self.document = fitz.open(path)
    self.pages=[ None for i in range(self.get_n_pages())]
    
  def paint_page(self,page,ctx):
    ctx.set_source_surface(self.get_page(page),0,0)
    ctx.paint()

  def get_n_pages(self):
    return self.document.pageCount

  def get_size_of_page(self,page):
    p=self.get_page(page)
    return (p.get_width(),p.get_height())
    
  def get_page(self,page):
    if self.pages[page]:
      return self.pages[page]
    else:
      self.pages[page]=self.get_page_img(page)
      return self.pages[page]

  def get_page_img(self,page):
    p=self.document.loadPage(page)
    pix = p.getPixmap()
    #gtk.gdk.pixbuf_new_from_data(pix.samples,gtk.gdk.COLORSPACE_RGB,True,pix.n,pix.width,pix.height,pix.stride)
    return cairo.ImageSurface.create_from_png(io.BytesIO(pix.getPNGData()))

  
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
    self.PREFIX_SETVARAT="@set@temp@vars@"
    self.SUFFIX_SETVARAT=""
    self.PREFIX_ROUNDRECTANGLEAT=""
    self.SUFFIX_ROUNDRECTANGLEAT="@roundrectangle"
    self.PREFIX_TABLEAT="@table@"
    self.SUFFIX_TABLEAT=""
    self.PREFIX_TABLEROWAT="@table@row@"
    self.SUFFIX_TABLEROWAT=""
    self.PREFIX_TABLE="tableform"
    self.SUFFIX_TABLE=""
    self.PREFIX_TABLECOL="col"
    self.SUFFIX_TABLECOL=""
    self.PREFIX_TABLECOLAT="@table@col@"
    self.SUFFIX_TABLECOLAT=""
    self.SUFFIX_PAGEATFIRST="@at@first@"
    self.SUFFIX_PAGENONEAT="@none@"
    self.SUFFIX_PAGEPDFAT="@pdf@"
    self.PREFIX_PAGENAMEBASE="pageNo"
    self.SUFFIX_PAGENAMEBASE=""
    
    self.FINALROW_HOOK_NAME="\\final@row@hook"
    self.SUFFIX_LOCALCOMMANDS="@"+projectdata.localcommandsuffix+"@nu@"
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
    return "\\"+self.PREFIX_SETVARAT+name+self.SUFFIX_SETVARAT+'@'+self.SUFFIX_LOCALCOMMANDS
  def roundrectangleATname(self,name):
    return "\\"+self.PREFIX_ROUNDRECTANGLEAT+name+self.SUFFIX_ROUNDRECTANGLEAT+'@'+self.SUFFIX_LOCALCOMMANDS
  def tablerowsATname(self,i):
    return "\\"+self.PREFIX_TABLEROWAT+self.int2alphabet(i)+self.SUFFIX_TABLEROWAT+'@'+self.SUFFIX_LOCALCOMMANDS
  def tableATname(self,i):
    return  "\\"+self.PREFIX_TABLEAT+self.int2alphabet(i)+self.SUFFIX_TABLEAT+'@'+self.SUFFIX_LOCALCOMMANDS
  def tablename(self,i):
    return self.PREFIX_TABLE+self.int2alphabet(i)+self.SUFFIX_TABLE
  def tablecolname(self,i):
    return "\\"+self.PREFIX_TABLECOL+self.int2alphabet(i)+self.SUFFIX_TABLECOL
  def tablecolATname(self,i):
    return "\\"+self.PREFIX_TABLECOLAT+self.int2alphabet(i)+self.SUFFIX_TABLECOLAT+'@'+self.SUFFIX_LOCALCOMMANDS

  def pagename_base(self,n):
    return self.PREFIX_PAGENAMEBASE+self.int2alphabet(n)+self.SUFFIX_PAGENAMEBASE
  
  def page_atfirst(self,n):
    return "\\"+self.pagename_base(n)+self.SUFFIX_PAGEATFIRST+'@'+self.SUFFIX_LOCALCOMMANDS
  def pagename_none(self,n):
    return self.pagename_base(n)+self.SUFFIX_PAGENONEAT+'@'+self.SUFFIX_LOCALCOMMANDS
  def pagename_pdf(self,n):
    return self.pagename_base(n)+self.SUFFIX_PAGEPDFAT+'@'+self.SUFFIX_LOCALCOMMANDS
  
  def pagename_frontend(self,n):
    return self.pagename_base(n)

  def pdffilename(self):
    return self.projectdata.bgimagepath
  
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

  def formfrontenddef_env(self,name,projectname,boxname,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    r=r +r'\newenvironment{'
    r=r + name
    r=r +r'}{\begin{nu@documentonform@put@box@env}{'
    r=r + projectname
    r=r +r'}{'
    r=r + boxname
    r=r +r'}}{\end{nu@documentonform@put@box@env}}'
    return r

  def formfrontenddef_com(self,name,projectname,boxname,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    r=r +r'\newcommand{'+"\\"
    r=r +name
    r=r +r'}[1]{\nu@documentonform@put@box@com{'
    r=r + projectname
    r=r +r'}{'
    r=r + boxname
    r=r +r'}{#1}}'
    return r

  def formfrontenddef_checkmark(self,name,projectname,boxname,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}{\nu@documentonform@put@checkmark@com{'
    r=r + projectname
    r=r +r'}{'
    r=r + boxname
    r=r +r'}}'
    return r

  def formfrontenddef_strike(self,name,projectname,boxname,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}{\nu@documentonform@put@strike@com{'
    r=r + projectname
    r=r +r'}{'
    r=r + boxname
    r=r +r'}}'
    return r

  def formfrontenddef_rule(self,name,projectname,boxname,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""
    
    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}{\nu@documentonform@put@rule@com{'
    r=r + projectname
    r=r +r'}{'
    r=r + boxname
    r=r +r'}}'
    return r

  def formfrontenddef_check_circle(self,name,projectname,boxname,as_comment=False):
    if as_comment:
      r="% "
    else:
      r=""

    r=r +r'\newcommand{'+"\\"
    r=r + name
    r=r +r'}{\nu@documentonform@put@oval@com{'
    r=r + projectname
    r=r +r'}{'
    r=r + boxname
    r=r +r'}}'
    return r


  def formfrontenddef(self,boxdata,projectname):
    r=[]
    as_comment=not(boxdata.type==BoxData.TYPE_ENVIRONMENT)
    r.append(self.formfrontenddef_env(boxdata.name,projectname,boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_COMMAND)
    r.append(self.formfrontenddef_com(boxdata.name,projectname,boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_CHECKMARK)
    r.append(self.formfrontenddef_checkmark(boxdata.name,projectname,boxdata.name,as_comment))
    
    as_comment=not(boxdata.type==BoxData.TYPE_STRIKE)
    r.append(self.formfrontenddef_strike(boxdata.name,projectname,boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_RULE)
    r.append(self.formfrontenddef_rule(boxdata.name,projectname,boxdata.name,as_comment))

    as_comment=not(boxdata.type==BoxData.TYPE_CHECK_CIRCLE)
    r.append(self.formfrontenddef_check_circle(boxdata.name,projectname,boxdata.name,as_comment))
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
  
  def def_page_atfirst(self,n):
    return r'\newcommand{'+self.page_atfirst(n)+r'}{}'

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
% Please redefine the command '''+self.page_atfirst(0)+r'''
% if you want to do something whenever '''+self.pagename_frontend(0)+r''' is called.
%
% Please redefine \baseuplength
% if you want to move background image up.
%
% Boxcommands, e.g. \boxIDa, 
% between \begin{groupedcolumns} and \end{groupedcolumns}
% use common top margin.
% The command \nextrow in the environment updates the margin.
%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Definition of basic commands
\NeedsTeXFormat{LaTeX2e}
\RequirePackage{documentonform}

\newif\if@PDF@image@type@nu@
\@PDF@image@type@nu@true
\newif\if@js@basecls@nu@
\@js@basecls@nu@false

\DeclareOption{pdf}{\@PDF@image@type@nu@true}
\DeclareOption{none}{\@PDF@image@type@nu@false}
\DeclareOption{js}{\@js@basecls@nu@true}
\ProcessOptions\relax
%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
  
  def get_style_code(self):
    r="%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    r=r+self.common_command()
    r=r+r'\nu@input@json@project@data{'+self.projectdata.localcommandsuffix+'}{projectdata.json}'+"\n"

    page_atfirst=""
    page_def=""
    page_front=""
    form_front=""

    for i in self.projectdata.get_pages_with_boxdata():
      page_front=page_front+"\n"+self.pagedef_frontend(i)
      page_def=page_def+"\n"+self.pagedef_woimage(i)
      page_def=page_def+"\n"+self.pagedef_pdf(i)
      page_atfirst=page_atfirst+"\n"+self.def_page_atfirst(i)
      form_front=form_front+"\n% page "+str(i+1)+" i.e.," +self.int2alphabet(i)
      for boxdata in self.projectdata.x_boxdata_in_the_page(i):
        #form_def=form_def+"\n"+self.setvardef(boxdata)
        #form_front=form_front+"\n\n"+self.setvardef(boxdata)
        #form_def=form_def+"\n"+self.roundcircledef(boxdata)+"\n\n"
        form_front=form_front+"\n\n"+self.formfrontenddef(boxdata,self.projectdata.localcommandsuffix)
        form_front=form_front+"\n"
        
    table_backend=""
    table_front=""
    for tabledata in self.projectdata.tables:
      table_backend=table_backend+"\n"+self.tablebackenddef(tabledata)
      table_front=table_front+"\n"+self.tablefrontenddef(tabledata)
    r=r+"%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Backend commands for pages."
    r=r+page_def
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Backend commands for table forms."
    r=r+table_backend
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Forntend commands of boxes\n"
    r=r+form_front
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Forntend commands of pages\n"
    r=r+page_front
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Hooked commands\n"
    r=r+page_atfirst
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n% Forntend commands of table forms\n"
    r=r+table_front
    r=r+"\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
    return r


  def get_sample_makefile(self,sample_file,style_file):
    r="LATEX=latex\nDVI2PDF=dvipdfmx\n"
    r=r+"STYLEFILE="+style_file+"\n\n"
    
    r=r+"TEXFILE="+sample_file+"\n\n"
    r=r+"all: pdf\ndvi: ${TEXFILE}.dvi\npdf: ${TEXFILE}.pdf\n\n"
    r=r+"${TEXFILE}.dvi: ${TEXFILE}.tex ${STYLEFILE}.sty documentonform.sty\n\t${LATEX} ${TEXFILE} && ${LATEX} ${TEXFILE}\n"
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
      TableData.serialnum=TableData.serialnum+1
    else:
      self.id_as_int=id_as_int
      TableData.serialnum=max(TableData.serialnum,id_as_int)+1
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
    vbox=Gtk.VBox()
    self.vbox=vbox
    label=Gtk.Label()
    label.set_markup(message)
    vbox.pack_start(label,False,False,10)
    table=Gtk.Table(n_rows=2,n_columns=12)
    vbox.add(table)

    label=Gtk.Label()
    label.set_markup("Id")
    table.attach(label,1,2,1,2)
    entry=Gtk.Entry()
    table.attach(entry,2,3,1,2)
    entry.set_text(str(boxdata.id))
    entry.set_editable(False)

    label=Gtk.Label()
    label.set_markup("Name")
    table.attach(label,1,2,2,3)
    entry=Gtk.Entry()
    self.entry_name=entry
    entry.set_text(str(boxdata.name))
    table.attach(entry,2,3,2,3)

    label=Gtk.Label()
    label.set_markup("sample text")
    table.attach(label,1,2,3,4)
    entry=Gtk.TextView()
    self.entry_sampletext=entry
    entry.get_buffer().set_text(str(boxdata.sampletext))
    self.entry_sampletext=entry
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    sw.add(entry) 
    table.attach(sw,2,3,3,4)

    label=Gtk.Label()
    label.set_markup("virtical align")
    table.attach(label,1,2,4,5)
    combobox = Gtk.ComboBoxText()
    for i,(text,v) in enumerate(self.COMBO_VALIGN):
      combobox.append_text(text)
      if boxdata.valign==v:
        combobox.set_active(i)
    self.entry_valign=combobox
    table.attach(combobox,2,3,4,5)

    label=Gtk.Label()
    label.set_markup("horizontal align")
    table.attach(label,1,2,5,6)
    combobox = Gtk.ComboBoxText()
    for i,(text,v) in enumerate(self.COMBO_HALIGN):
      combobox.append_text(text)
      if boxdata.halign==v:
        combobox.set_active(i)
    self.entry_halign=combobox
    table.attach(combobox,2,3,5,6)

    label=Gtk.Label()
    label.set_markup("type")
    table.attach(label,1,2,6,7)
    combobox = Gtk.ComboBoxText()
    for i,(text,v) in enumerate(self.COMBO_TYPE):
      combobox.append_text(text)
      if boxdata.type==v:
        combobox.set_active(i)
    self.entry_type=combobox
    table.attach(combobox,2,3,6,7)

    label=Gtk.Label()
    label.set_markup("page")
    table.attach(label,1,2,7,8)
    adjustment = Gtk.Adjustment(value=boxdata.page,lower=0,upper=projectdata.document.get_n_pages(),step_increment=1)
    entry=Gtk.SpinButton()
    entry.set_adjustment(adjustment)
    entry.set_value(boxdata.page)
    self.entry_page=entry
    table.attach(entry,2,3,7,8)

    label=Gtk.Label()
    label.set_markup("top")
    table.attach(label,1,2,8,9)
    adjustment = Gtk.Adjustment(value=boxdata.y_1,lower=0,upper=projectdata.lheight,step_increment=1,page_increment=1)
    entry=Gtk.SpinButton()
    entry.set_adjustment(adjustment)
    entry.set_value(boxdata.y_1)
    self.entry_y1=entry
    table.attach(entry,2,3,8,9)
    
    label=Gtk.Label()
    label.set_markup("bottom")
    table.attach(label,1,2,9,10)
    adjustment = Gtk.Adjustment(value=boxdata.y_2,lower=0,upper=projectdata.lheight,step_increment=1,page_increment=1)
    entry=Gtk.SpinButton()
    entry.set_adjustment(adjustment)
    entry.set_value(boxdata.y_2)
    self.entry_y2=entry
    table.attach(entry,2,3,9,10)

    label=Gtk.Label()
    label.set_markup("left")
    table.attach(label,1,2,10,11)
    adjustment = Gtk.Adjustment(value=boxdata.x_1,lower=0,upper=projectdata.lwidth,step_increment=1,page_increment=1)

    entry=Gtk.SpinButton()
    entry.set_adjustment(adjustment)
    entry.set_value(boxdata.x_1)
    self.entry_x1=entry
    table.attach(entry,2,3,10,11)

    label=Gtk.Label()
    label.set_markup("right")
    table.attach(label,1,2,11,12)
    adjustment = Gtk.Adjustment(value=boxdata.x_2,lower=0,upper=projectdata.lwidth,step_increment=1,page_increment=1)
    entry=Gtk.SpinButton()
    entry.set_adjustment(adjustment)
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
    self.boxdata.sampletext=self.entry_sampletext.get_buffer().get_text(st,end,False)
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
    vbox=Gtk.VBox()
    self.vbox=vbox
    label=Gtk.Label()
    label.set_markup(message)
    vbox.pack_start(label,False,False,10)
    table=Gtk.Table(n_rows=2,n_columns=10)
    vbox.add(table)

    label=Gtk.Label()
    label.set_markup("virtical align")
    table.attach(label,1,2,4,5)
    combobox = Gtk.ComboBoxText()
    for i,(text,v) in enumerate(self.COMBO_VALIGN):
      combobox.append_text(text)
      #if boxdata.valign==v:
      #  combobox.set_active(i)
    combobox.set_active(1)
    self.entry_valign=combobox
    table.attach(combobox,2,3,4,5)

    label=Gtk.Label()
    label.set_markup("horizontal align")
    table.attach(label,1,2,5,6)
    combobox = Gtk.ComboBoxText()
    for i,(text,v) in enumerate(self.COMBO_HALIGN):
      combobox.append_text(text)
      #if boxdata.halign==v:
      #  combobox.set_active(i)
    combobox.set_active(1)
    self.entry_halign=combobox
    table.attach(combobox,2,3,5,6)

    label=Gtk.Label()
    label.set_markup("type")
    table.attach(label,1,2,6,7)
    combobox = Gtk.ComboBoxText()
    for i,(text,v) in enumerate(self.COMBO_TYPE):
      combobox.append_text(text)
      #if boxdata.type==v:
      #  combobox.set_active(i)
    combobox.set_active(1)
    self.entry_type=combobox
    table.attach(combobox,2,3,6,7)

    label=Gtk.Label()
    label.set_markup("page")
    table.attach(label,1,2,7,8)
    adjustment = Gtk.Adjustment(value=current_page,lower=0,upper=projectdata.document.get_n_pages(),step_increment=1)
    entry=Gtk.SpinButton()
    entry.set_adjustment(adjustment)
    entry.set_value(current_page)
    self.entry_page=entry
    table.attach(entry,2,3,7,8)

    label=Gtk.Label()
    label.set_markup("t,b;t,b;...;t,b")
    table.attach(label,1,2,8,9)
    entry=Gtk.Entry()
    self.entry_yy=entry
    entry.set_text("")
    table.attach(entry,2,3,8,9)

    label=Gtk.Label()
    label.set_markup("l,r;l,r;...;l,r")
    table.attach(label,1,2,9,10)
    entry=Gtk.Entry()
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

    vbox=Gtk.VBox()
    self.vbox=vbox

    store = Gtk.ListStore (str,str,str, int, int,int,int,int, str,str,str)
    treeview=Gtk.TreeView(model=store)
    self.treeview=treeview
    
    #treeview.set_rules_hint(True)
    treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    
    
    tvcolumn = Gtk.TreeViewColumn('page')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 3)
    treeview.set_reorderable(True)

    tvcolumn = Gtk.TreeViewColumn('id')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 0)
    
    tvcolumn = Gtk.TreeViewColumn('Neme')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 1)
    
    tvcolumn = Gtk.TreeViewColumn('y')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 6)
    treeview.set_reorderable(True)


    tvcolumn = Gtk.TreeViewColumn("y'")
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 7)
    treeview.set_reorderable(True)
    
    tvcolumn = Gtk.TreeViewColumn('x')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 4)
    treeview.set_reorderable(True)

    tvcolumn = Gtk.TreeViewColumn("x'")
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 5)
    treeview.set_reorderable(True)


    tvcolumn = Gtk.TreeViewColumn('valign')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 8)
    treeview.set_reorderable(True)

    tvcolumn = Gtk.TreeViewColumn('halign')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 9)
    treeview.set_reorderable(True)

    tvcolumn = Gtk.TreeViewColumn('type')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 10)
    treeview.set_reorderable(True)



    tvcolumn = Gtk.TreeViewColumn('Sample Text')
    treeview.append_column(tvcolumn)
    cell = Gtk.CellRendererText()
    tvcolumn.pack_start(cell, True)
    tvcolumn.add_attribute(cell, 'text', 2)
    treeview.set_reorderable(True)
    
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    sw.add(treeview) 
    vbox.add(sw)


    hbox = Gtk.HButtonBox() 
    vbox.pack_start(hbox,False,False,0)
    hbox.set_layout(Gtk.ButtonBoxStyle.END)
    self.buttonbox=hbox
    
#    button = Gtk.Button(stock=Gtk.STOCK_NEW)
#    button = Gtk.Button.new_with_mnemonic("NEW")
    button = Gtk.Button.new_from_icon_name("list-add",Gtk.IconSize.LARGE_TOOLBAR)

    hbox.add(button)
    self.button_new=button
#    button = Gtk.Button(stock=Gtk.STOCK_REMOVE)
    button = Gtk.Button.new_from_icon_name("list-remove",Gtk.IconSize.LARGE_TOOLBAR)
    hbox.add(button)
    self.button_remove=button
    
    button = Gtk.Button(stock=Gtk.STOCK_EDIT)
    #button = Gtk.Button.new_from_icon_name("list-edit",Gtk.IconSize.LARGE_TOOLBAR)
    #button = Gtk.Button.new_from_icon_name("gtk-edit",Gtk.IconSize.LARGE_TOOLBAR)
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
    #self.treeview.scroll_to_cell(path)
    
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

class LayoutOverBoxes(Gtk.Layout):
  def __init__(self,projectdata):
    Gtk.Layout.__init__(self)
    self.message='test text'
    self.width = self.height = 0
    self.connect('size-allocate', self.on_self_size_allocate)
    self.connect('draw', self.on_self_expose_event)
    self.projectdata=projectdata
    self.page=0

  def refresh_preview(self):
    if self.get_window():
      self.get_window().invalidate_rect(self.get_allocation(),True) 

  def set_page(self,page):
    n=self.projectdata.document.get_n_pages()
    if n>0:
      self.page=page % n
    else:
      self.page=page
    self.refresh_preview()


    
  def on_self_size_allocate(self, widget, allocation):
    self.width = allocation.width
    self.height = allocation.height

  def on_self_expose_event(self, widget, event):
    #ctx = widget.get_bin_window().cairo_create()
    ctx = widget.get_window().cairo_create()
    if not self.projectdata:
      return    
    self.projectdata.document.paint_page(self.page,ctx)
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



class Bar(Gtk.DrawingArea):
  def __init__(self,direction,margin):
    Gtk.DrawingArea.__init__(self)
    self.width = self.height = 0
    self.direction=direction
    self.connect('size-allocate', self.on_self_size_allocate)
    self.connect('draw', self.on_self_expose_event)
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
    ctx = widget.get_window().cairo_create()
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

class SpinButtonForBarOnLayout(Gtk.SpinButton):
  def __init__(self,adj_max,id_adj,id_spb):
    adj=Gtk.Adjustment(value=0,lower=0,upper=adj_max,step_increment=1)
    Gtk.SpinButton.__init__(self)
    self.set_adjustment(adj)
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

class BarOnLayout(Gtk.EventBox):
  MASK_VIRTICAL_BAR=2
  MASK_OPPOSIT_DIRECTION=1
  LINEWIDTH=1
  def __init__(self,direction,max_x,max_y,spinbuttonforbar,griddata,current_page):
    Gtk.EventBox.__init__(self)
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
      box=Gtk.HBox()
      label_box=Gtk.VBox()
      label_box.pack_start(Gtk.HSeparator(),False,False,0)
    else:
      self.width=max_x
      self.height=self.LINEWIDTH
      self.margin=(13+4*griddata.id)%self.width
      box=Gtk.VBox()
      label_box=Gtk.HBox()
      label_box.pack_start(Gtk.VSeparator(),False,False,0)

    drawingarea = Bar(direction,self.margin)
    self.drawingarea=drawingarea
    drawingarea.set_size_request(self.width,self.height)
    self.set_visible(True)
    self.set_visible_window(False)

    self.add(box)
    box.add(drawingarea)
    label=Gtk.Label()
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


  def fit_to_size(self,width,height):
    if self.direction & self.MASK_VIRTICAL_BAR:
      if height > self.height: 
        self.height=max(self.max_y,height)
        self.drawingarea.height=self.height
        self.drawingarea.set_size_request(self.width,self.height)
    else:
      if width > self.width:
        self.width=max(self.max_x,width)
        self.drawingarea.width=self.width
        self.drawingarea.set_size_request(self.width,self.height)


    


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
      self.get_parent().refresh_preview()
    else:
      if v<0:
        v=0
      if self.max_y<v:
        v=self.max_y
      self.griddata.value=int(v)
      self.move_virtical(v)
      self.get_parent().refresh_preview()


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
    self.get_parent().move(self,self.x,y)
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
    self.get_parent().move(self, x, self.y)
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
      self.margin_x =self.margin_x-int(self.get_parent().get_parent().get_hadjustment().get_value())


      self.margin_y =self.margin_y-int(self.get_parent().get_parent().get_vadjustment().get_value())
    return True

  def button_release_event(self,widget, event):
    if not self.draging:
      return True
    (p,x,y,state)=self.get_parent().get_window().get_device_position(event.device)
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
    (p,x,y,state)=self.get_parent().get_window().get_device_position(event.device)
    if state & Gdk.ModifierType.BUTTON1_MASK:
      if self.direction & self.MASK_VIRTICAL_BAR:
        self.move_horizontal(x-self.margin_x)
      else:
        self.move_virtical(y-self.margin_y)
    return True





##################
class BoxDataDialog(Gtk.Dialog):
  def __init__(self,title=None, parent=None, destroy_with_parent=False,boxdata=None,message="",projectdata=None):
    Gtk.Dialog.__init__(self,title=title,parent=parent,destroy_with_parent=destroy_with_parent)
    self.area=BoxDataEntryArea(boxdata,message,projectdata)
    self.vbox.pack_start(self.area.get_box(),True,True,0)

  def get_boxdata(self):
    return self.area.update_and_get_boxdata()

class TableDataDialog(Gtk.Dialog):
  def __init__(self,title=None, parent=None, destroy_with_parent=False,message="",projectdata=None,current_page=0):
    Gtk.Dialog.__init__(self,title=title,parent=parent,destroy_with_parent=destroy_with_parent)
    self.area=TableDataEntryArea(message,projectdata,current_page)
    self.vbox.pack_start(self.area.get_box(),True,True,0)

  def get_tabledata(self):
    return self.area.get_tabledata()

class HoganDialog(Gtk.Dialog):
  def __init__(self,title=None, parent=None,destroy_with_parent=True, projectdatabib=None,p=0):
    Gtk.Dialog.__init__(self,title=title,parent=parent,destroy_with_parent=destroy_with_parent)
    projectdata=projectdatabin.document_data
    self.area=LayoutOverBoxesWithHoganArea(projectdata,p)
    self.vbox.pack_start(self.area.get_box(),True,True,0)
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
    
    box = Gtk.VBox(homogeneous=False,spacing=0)
    box.show()
    layout = LayoutOverBoxes(self.projectdata)
    self.layout = layout
    self.layout.set_page(p)
    layout.set_size(self.projectdata.lwidth, self.projectdata.lheight)    
    layout.connect("size-allocate", self.layout_resize)
    layout.show()
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    sw.add(layout) 
    box.pack_start(sw, True, True, 0)

    coordinate_hbox=Gtk.HBox(spacing=20)
    self.coordinate_hbox=coordinate_hbox

    self.coordinate_hbox.add(Gtk.VSeparator())

    hbox=Gtk.HBox()
    coordinate_hbox.add(hbox)
    label=Gtk.Label()
    hbox.add(label)
    label.set_markup("Current page: ")
    
    adj = Gtk.Adjustment(value=p, lower=0,upper=self.projectdata.document.get_n_pages()-1, step_increment=1)
    entry=Gtk.SpinButton()
    entry.set_adjustment(adj)

    entry.connect("changed", self.on_page_changed_event)
    hbox.add(entry)

    
    #self.coordinate_hbox.add(Gtk.VSeparator())
    self.coordinate_hbox.add(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

    hbox=Gtk.HBox()
    self.coordinate_hbox.add(hbox)
    label=Gtk.Label()
    hbox.add(label)
    label.set_markup("Forcused grid: ")
    adj = Gtk.Adjustment(value=p, lower=0,upper=-1, step_increment=1)
    entry=Gtk.SpinButton()
    entry.set_adjustment(adj)
    hbox.add(entry)

    hbox=Gtk.HBox()
    self.coordinate_hbox.add(hbox)
    label=Gtk.Label()
    hbox.add(label)
    label.set_markup("Value: ")
    w=self.projectdata.lwidth
    h=self.projectdata.lheight
    self.spb=SpinButtonForBarOnLayout(max(w,h),adj,entry)
    hbox.add(self.spb)
    self.spb.connect("changed", self.spb.move_bar_on_changed)
    entry.connect("changed", self.spb.set_current_bar_on_changed)

    
    self.coordinate_hbox.add(Gtk.VSeparator())
  
    hbox = Gtk.HButtonBox()
    coordinate_hbox.add(hbox)
    hbox.set_layout(Gtk.ButtonBoxStyle.CENTER)
    
    combobox = Gtk.ComboBoxText()
    hbox.add(combobox)
    combobox.append_text("---")
    combobox.append_text(" | ")
    combobox.connect('changed', self.toggle_ruler_direction_onchange)
    self.new_ruler_will_be_horizontal=True
    combobox.set_active(0)
    

    button = Gtk.Button.new_from_icon_name("list-add",Gtk.IconSize.LARGE_TOOLBAR)
    hbox.add(button)
    self.button_edit=button
    button.connect('clicked', self.add_new_ruler_onclick)


    self.coordinate_hbox.add(Gtk.VSeparator())

    checkbutton= Gtk.CheckButton(label="hide all")
    checkbutton.show()
    checkbutton.connect("toggled", self.on_toggle_hide_grid)
    self.coordinate_hbox.add(checkbutton)

    self.coordinate_hbox.add(Gtk.VSeparator())


    self.rulers=[]

    coordinate_hbox.show_all()
    box.pack_start(coordinate_hbox, False, False, 0)

    hbox=Gtk.HBox()
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
    bar.fit_to_size(self.layout.get_allocated_width(),self.layout.get_allocated_height())
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
    rectangle = widget.get_allocation()
    if rectangle.width > self.projectdata.lwidth or rectangle.height > self.projectdata.lheight:
      lwidth = max(rectangle.width, self.projectdata.lwidth)
      lheight = max(rectangle.height, self.projectdata.lheight)
      widget.set_size(lwidth, lheight)
    for bar in self.rulers:
      bar.fit_to_size(lwidth, lheight)
      bar.queue_draw()
    
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
  
  @classmethod
  def new_from_json(cls,uri):
    p=urllib.parse.urlparse(uri)
    path=urllib.parse.unquote(p.path)
    (destdir,filename)=os.path.split(path)
    f = open(path)
    prev_proj= json.load(f)
    bgimagepath=prev_proj["bgimagepath"]
    bgimagefullpath=os.path.join(destdir,bgimagepath)
    prev_proj["pdfuri"]='file://'+urllib.request.pathname2url(bgimagefullpath)
    return ProjectData(prev_proj,bgimagepath,bgimagefullpath)

  @classmethod
  def new_from_pdf(cls,uri):
    p=urllib.parse.urlparse(uri)
    path=urllib.parse.unquote(p.path)
    (destdir,filename)=os.path.split(path)
    (base,ext)=os.path.splitext(filename)
    bgimagefullpath=path
    bgimagepath=filename
    prev_proj={}
    prev_proj["pdfuri"]=uri
    prev_proj["stylename"]=base
    return ProjectData(prev_proj,bgimagepath,bgimagefullpath)

  def __init__(self,prev_proj,bgimagepath,bgimagefullpath):
    self.bgimagepath=bgimagepath
    self.bgimagefullpath=bgimagefullpath

    self.set_document(prev_proj["pdfuri"])
    if "stylename" in prev_proj:
      self.stylename=prev_proj["stylename"]
    else:
      self.stylename=None
    if "localcommandsuffix" in prev_proj:
      self.localcommandsuffix=prev_proj["localcommandsuffix"]
    else:
      self.localcommandsuffix=re.sub(r'[^a-zA-Z]','',self.stylename)
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
      self.document=get_pdfdocument_from_uri(uri)
    else:
      self.document=None
    if self.document:
      width = 0
      height = 0
      for i in range(self.document.get_n_pages()):
        (w,h)=self.document.get_size_of_page(i)
        self.boundingboxes.append((0,0,w,h))
        if width<w:
          width=w
        if height<h:
          height=h

      self.lwidth = int(width)
      self.lheight = int(height)
      
    else:
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


  def output_to_zipfile(self,destzip,rootdir):
    print_log("writing imagefiles....")
    afd=applicationFormData(self)
    afd.create_bgimage_file(self.bgimagefullpath,destzip,rootdir)

    print_log("writing the style file....")
    stypath=os.path.join(rootdir,self.stylename+".sty")
    inf=zipfile.ZipInfo(stypath)
    destzip.writestr(inf,afd.get_style_code())

    print_log("writing a sample file....")
    samplepath=os.path.join(rootdir,self.samplepath)
    inf=zipfile.ZipInfo(samplepath)
    destzip.writestr(inf,afd.get_sample_code(self.stylename))

    print_log("writing Makefile....")
    makefilepath=os.path.join(rootdir,self.makefilepath)
    inf=zipfile.ZipInfo(makefilepath)
    destzip.writestr(inf,afd.get_sample_makefile(self.samplebase,self.stylename))

    print_log("writing this project data....")
    jsonfilepath=os.path.join(rootdir,self.jsonpath)
    inf=zipfile.ZipInfo(jsonfilepath)
    destzip.writestr(inf,self.dump_as_json())
    
    for inf in destzip.infolist():
      inf.external_attr = 0o755 << 16
      inf.create_system = 0
    destzip.close()
    print_log("done.")

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
    d["localcommandsuffix"]=self.localcommandsuffix
    d["boxes"]=[box.dump_as_dictionary() for box in self.boxes]
    d["grids"]=[grid.dump_as_dictionary() for grid in self.grids]
    d["tables"]=[table.dump_as_dictionary() for table in self.tables]
    return d
  
  def dump_as_json(self):
    d=self.dump_as_dictionary()
    return json.dumps(d,indent=2)

  def new_boxdata_at_page(self,page):
    p=page
    x1=0
    x2=1
    y1=2
    y2=3

    xx=[(griddata.value,griddata.id) for griddata in self.grids if not griddata.is_horizontal  if griddata.page==p]
    if len(xx)>0:
      xx.sort()
      x1=xx[0][1]
      x2=xx[-1][1]
    else:
      xx=[(griddata.value,griddata.id) for griddata in self.grids if not griddata.is_horizontal]
      if len(xx)>0:
        xx.sort()
        x1=xx[0][1]
        x2=xx[-1][1]
    yy=[(griddata.value,griddata.id) for griddata in self.grids if  griddata.is_horizontal and griddata.page==p]
    if len(yy)>0:
      yy.sort()
      y1=yy[0][1]
      y2=yy[-1][1]
    else:
      yy=[(griddata.value,griddata.id) for griddata in self.grids if griddata.is_horizontal]
      if len(yy)>0:
        yy.sort()
        y1=yy[0][1]
        y2=yy[-1][1]

    return BoxData(p,x1,x2,y1,y2)

class ProjectApplicationData:
  def __init__(self):
    self.current_page=0

  def set_current_page(self,p):
    self.current_page=p

class ProjectMetaData:
  def __init__(self,uri):
    p=urllib.parse.urlparse(uri)
    path=urllib.parse.unquote(p.path)
    (dirname,filename)=os.path.split(path)
    self.current_directory=dirname

  def get_current_dirctory(self):
    return self.current_directory
  
class ProjectDataBin:
  def __init__(self,meta_data,document_data,application_data):
    self.application_data=application_data
    self.document_data=document_data
    self.meta_data=meta_data

  @classmethod
  def new_from_uri(cls,uri):
    p=urllib.parse.urlparse(uri)
    path=urllib.parse.unquote(p.path)
    (destdir,filename)=os.path.split(path)
    (base,ext)=os.path.splitext(filename)
    if ext==".json":
      document_data=ProjectData.new_from_json(uri)
    else:
      document_data=ProjectData.new_from_pdf(uri)
    meta_data=ProjectMetaData(uri)
    application_data=ProjectApplicationData()
    return ProjectDataBin(meta_data,document_data,application_data)

class AFMMainWindow(Gtk.ApplicationWindow):
  def __init__(self, uri, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.projectdatabin=ProjectDataBin.new_from_uri(uri)
    self.projectdata=self.projectdatabin.document_data
    self.preview=None    
    self.build_ui()
    self.connect_menu_actions()
    self.set_default_size(360, 300)
    self.show_all()

  def connect_menu_actions(self):
    action = Gio.SimpleAction.new("saveas", None)
    action.connect("activate", lambda widget,parm:self.save_as())
    self.add_action(action)

    action = Gio.SimpleAction.new_stateful("toggle_preview", None, GLib.Variant.new_boolean(False))
    action.connect("change-state", lambda   action,value: self.toggle_preview_dialog())
    self.add_action(action)
    self.toggle_preview_action=action

    
  def build_ui(self):
    box=Gtk.Box()
    box.set_orientation(Gtk.Orientation.VERTICAL)
    self.add(box)

    listarea=BoxDataListArea(self)
    box.pack_start(listarea.get_vbox(),True,True,0)
    self.listarea=listarea
    (button_new,button_remove,button_edit)=listarea.get_buttons()
    button_new.connect('clicked', self.on_click_new)
    button_remove.connect('clicked', self.on_click_remove)
    button_edit.connect('clicked', self.on_click_edit)

    hbbox = Gtk.HButtonBox()
    listarea.get_buttonbox().pack_start(hbbox,False,False,0)

    hbbox.set_layout(Gtk.ButtonBoxStyle.END)
    button = Gtk.Button.new_with_mnemonic("Add a table")
    button.connect('clicked', self.on_click_addtable)
    hbbox.add(button)

    hbbox = Gtk.HButtonBox() 
    listarea.get_vbox().pack_start(hbbox,False,False,0)
    hbbox.set_layout(Gtk.ButtonBoxStyle.END)

    hbbox.set_layout(Gtk.ButtonBoxStyle.END)
    #button = Gtk.Button.new_with_mnemonic("Show Grids/Preview")
    #button.connect('clicked', self.on_click_preview)
    button = Gtk.ToggleButton.new_with_mnemonic("Show Grids/Preview")
    self.toggle_preview_button_handler_id=button.connect("toggled",lambda widget:self.toggle_preview_dialog())
    self.toggle_preview_button=button
  
    

    hbbox.add(button)
    
    button = Gtk.Button.new_from_icon_name("document-save-as",Gtk.IconSize.LARGE_TOOLBAR)
    button.connect('clicked', lambda widget:self.save_as())
    hbbox.add(button)
    hbbox.show_all()


  def refresh_preview(self):
      if self.preview:
        self.preview.refresh_preview()

  def is_valid_boxdata(self,boxdata):
    if boxdata:
      return True
    else:
      return True

  def get_boxdata_by_dialog(self,boxdata,title,message):
    dialog=BoxDataDialog(title,None,True,boxdata,message,self.projectdata)
    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.REJECT,
                       Gtk.STOCK_OK,
                       Gtk.ResponseType.ACCEPT)
    r = dialog.run()
    if r==Gtk.ResponseType.ACCEPT:
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

  def confirm_and_add(self,boxdata):
    title="New box."
    message="Add the following box:"
    boxdata=self.get_valid_boxdata_by_dialog(boxdata,title,message)
    if boxdata:
      self.listarea.append_boxdata(boxdata)
      self.projectdata.add_boxdata(boxdata)
      self.refresh_preview()

  def on_click_new(self,widget):
    p=0
    if self.preview != None:
      p=self.preview.get_currentpage()
    boxdata=self.projectdata.new_boxdata_at_page(p)
    self.confirm_and_add(boxdata)

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

  def on_click_remove(self,widget):
    (model,iteralist,boxids)=self.listarea.get_selected_ids()
    if not boxids:
      return
    for (itera,boxid,) in zip(iteralist,boxids):
      self.confirm_and_remove_by_id(boxid,model,itera)

      
  def on_click_edit(self,widget):
    (model,iteralist,boxids)=self.listarea.get_selected_ids()
    if not boxids:
      return
    for (itera,boxid) in zip(iteralist,boxids):
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
    dialog=TableDataDialog(title,None,True,message,self.projectdata,current_page)
    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.REJECT,
                       Gtk.STOCK_OK,
                       Gtk.ResponseType.ACCEPT)
    r = dialog.run()
    if r==Gtk.ResponseType.ACCEPT:
      tabledata=dialog.get_tabledata()
    else:
      tabledata=None
    dialog.destroy()
    return tabledata

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
        
  def on_click_addtable(self,widget):
    self.confirm_and_addtable()
      
  #############################################################
  def save_as(self):
    dialog = Gtk.FileChooserDialog(title='Select zip file to save.',
                                   parent=self,
                                   action=Gtk.FileChooserAction.SAVE)
    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.REJECT,
                       Gtk.STOCK_SAVE,
                       Gtk.ResponseType.ACCEPT)
    dialog.set_current_folder(self.projectdatabin.meta_data.get_current_dirctory())
    dialog.set_current_name(self.projectdata.stylename+'-stylefile.zip')

    dialog.set_do_overwrite_confirmation(True)
    filter = Gtk.FileFilter()
    filter.set_name("ZIP files")
    filter.add_mime_type("application/x-compress")
    filter.add_mime_type("application/x-zip-compressed")
    filter.add_mime_type("application/zip")
    filter.add_mime_type("application/x-zip")
    filter.add_pattern("*.zip")
    dialog.add_filter(filter)
    filter = Gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    r = dialog.run()
    if r!=Gtk.ResponseType.ACCEPT:
      dialog.destroy()
      return
    destzipfilename=dialog.get_filename()
    dialog.destroy()
    print_log('creating '+destzipfilename+'.')
    rootdir=os.path.splitext(os.path.basename(destzipfilename))[0]
    destzip=zipfile.ZipFile(destzipfilename,'w')
    self.projectdata.output_to_zipfile(destzip,rootdir)

  def toggle_preview_dialog(self):
    self.toggle_preview_button.handler_block(self.toggle_preview_button_handler_id)
    if self.preview:
      self.preview.destroy()
      self.preview=None

      self.toggle_preview_button.set_active(False)
      self.toggle_preview_action.set_state(GLib.Variant.new_boolean(False))
    else:
      self.toggle_preview_button.set_active(True)
      self.toggle_preview_action.set_state(GLib.Variant.new_boolean(True))
      dialog=HoganDialog("Preview",None,True,self.projectdatabin,0)
      dialog.connect("delete_event", lambda widget,event:self.toggle_preview_dialog())
      dialog.show()
      self.preview=dialog
    self.toggle_preview_button.handler_unblock(self.toggle_preview_button_handler_id)



class AFMApplication(Gtk.Application):
  def __init__(self,*args, **kwargs):
    super().__init__(*args, **kwargs)
    self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)

    self.APP_NAME="AFM"
    self.APP_VERSION="3.0.0"
    self.APP_DESCRIPTION="AFM is not a fuzzy mule. Application Form Maker."
    self.APP_URL="https://github.com/a175/afm/"
    self.APP_LOGO_FILE=None
    #self.APP_LOGO_FILE="./icon.png"
    self.MENUBAR_XML_FILENAME =  "./afm_ui.xml"




  def do_startup(self):
    Gtk.Application.do_startup(self)
    self.build_menubar()
  def do_activate(self):
    self.select_file_and_open_as_new()

  def do_open(self,files,n_files,hint):
    for gfile in files:
      print(gfile.get_path(),gfile.get_uri())
      uri=gfile.get_uri()
    window=AFMMainWindow(uri,application=self)
    window.present()

  def select_file_and_open_as_new(self):
    dialog = Gtk.FileChooserDialog(title='Choose pdf file.',parent=None,action=Gtk.FileChooserAction.OPEN)
    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.REJECT,
                       Gtk.STOCK_OPEN,
                       Gtk.ResponseType.ACCEPT)
    filter = Gtk.FileFilter()
    filter.set_name("PDF files")
    filter.add_mime_type("application/pdf")
    filter.add_mime_type("application/x-pdf")
    filter.add_pattern("*.pdf")
    dialog.add_filter(filter)
    filter = Gtk.FileFilter()
    filter.set_name("project JSON files")
    filter.add_mime_type("application/json")
    filter.add_mime_type("application/x-json")
    filter.add_pattern("*"+ProjectData.DEFAULT_JSON_EXT)
    dialog.add_filter(filter)
    filter = Gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    r = dialog.run()
    if r==Gtk.ResponseType.ACCEPT:
      file=dialog.get_file()
      dialog.destroy()      
      self.open([file],"open_as_new")
    else:
      uri=None
      dialog.destroy()

  def build_menubar(self):
    builder = Gtk.Builder.new_from_file(self.MENUBAR_XML_FILENAME)
    menubar = builder.get_object("menubar")
    self.set_menubar(menubar)
    
    action = Gio.SimpleAction.new("open", None)
    action.connect("activate", self.on_open)
    self.add_action(action)
    
    action = Gio.SimpleAction.new("quit", None)
    action.connect("activate", self.on_quit)
    self.add_action(action)
    
    action = Gio.SimpleAction.new("about", None)
    action.connect("activate", self.on_about)
    self.add_action(action)
    
    action = Gio.SimpleAction.new("help", None)
    action.connect("activate", self.on_help)
    self.add_action(action)
    

  def on_quit(self,action,param):
    self.quit()

  def on_about(self, action, param):
    about_dialog = Gtk.AboutDialog()
    about_dialog.set_program_name(self.APP_NAME)
    about_dialog.set_version(self.APP_VERSION)
    about_dialog.set_website(self.APP_URL)
    about_dialog.set_comments(self.APP_DESCRIPTION)
    if self.APP_LOGO_FILE:
      pixbuf=GdkPixbuf.Pixbuf.new_from_file(self.APP_LOGO_FILE)
      about_dialog.set_logo(pixbuf)
    about_dialog.present()

    
  def on_help(self, action, param):
    help_dialog = Gtk.MessageDialog(flags=0,buttons=Gtk.ButtonsType.OK,text="Help")
    help_dialog.format_secondary_text("Help for AFM")
    link=Gtk.LinkButton.new_with_label("https://github.com/a175/afm/","link to help")
    link.show()
    contentarea=help_dialog.get_content_area()
    contentarea.add(link)
    help_dialog.run()
    help_dialog.destroy()


  def on_open(self,action,param):
    self.select_file_and_open_as_new()


def main():
  app=AFMApplication()
  app.run(sys.argv)

  
if __name__ == "__main__":
  main()

