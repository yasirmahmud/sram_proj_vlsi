; Compact reference-style 6T core: inverter pair centered, access FETs at sides.
; Horizontal reference poly straps are replaced with local Metal2 connections.
procedure(rect(cv layer x1 y1 x2 y2)
 dbCreateRect(cv list(layer "drawing") list(list(x1 y1) list(x2 y2))))
procedure(via12compact(cv x y gate)
 rect(cv "Via1" x-.035 y-.035 x+.035 y+.035)
 if(gate then rect(cv "Metal1" x-.07 y-.075 x+.07 y+.075)
 else rect(cv "Metal1" x-.065 y-.04 x+.065 y+.04))
 rect(cv "Metal2" x-.065 y-.04 x+.065 y+.04))
procedure(gateContact(cv x y bottom top)
 rect(cv "Poly" x-.07 bottom x+.07 top)
 rect(cv "Cont" x-.03 y-.03 x+.03 y+.03)
 via12compact(cv x y t))
procedure(port(cv name layer x1 y1 x2 y2)
 let((net fig)
 net=dbCreateNet(cv name)
 dbCreateTerm(net name if(member(name '("WL" "Vdd" "GND")) then "input" else "inputOutput"))
 fig=dbCreateRect(cv list(layer "pin") list(list(x1 y1) list(x2 y2)))
 dbCreatePin(net fig name)
 dbCreateLabel(cv list(layer "label") list((x1+x2)/2 (y1+y2)/2) name "centerCenter" "R0" "roman" .045)))
procedure(buildCompact(cellName pdWidth accessWidth)
 let((src cv nm bb x1 y1 x2 y2)
 src=dbOpenCellViewByType("reference" "sram_cell_layout_no_power" "layout" "" "r")
 cv=dbCopyCellView(src "sram_cell" cellName "layout" nil nil t)
 ; Set actual PCell geometry, not just a schematic CDF width string.
 foreach(i cv~>instances
   when(i~>cellName=="nmos1v"
    dbReplaceProp(i "fw" "float" if(member(i~>name '("NM0" "NM1")) then pdWidth else accessWidth))
    dbReplaceProp(i "w" "string" if(member(i~>name '("NM0" "NM1")) then sprintf(nil "%gn" pdWidth*1e9) else sprintf(nil "%gn" accessWidth*1e9)))
   ))
 ; Remove three horizontal poly interconnects and their two original contacts.
 foreach(s cv~>shapes
   when(s~>layerName=="Poly"
     bb=s~>bBox
     when(caadr(bb)-caar(bb) > cadadr(bb)-cadar(bb) dbDeleteObject(s))))
 foreach(v cv~>vias dbDeleteObject(v))
 ; Move storage-node Metal1 columns away from the new gate contacts.
 foreach(s cv~>shapes
   when(s~>layerName=="Metal1"
     bb=s~>bBox x1=caar(bb) y1=cadar(bb) x2=caadr(bb) y2=cadadr(bb)
     when(abs(x1+1.225)<.0001 && abs(x2+1.165)<.0001 && abs(y1-.575)<.0001
       dbDeleteObject(s) rect(cv "Metal1" -1.165 .23 -1.105 1.145))
     when(abs(x1+.71)<.0001 && abs(x2+.65)<.0001
       dbDeleteObject(s) rect(cv "Metal1" -.65 .23 -.59 1.245))
     when(abs(x1+1.81)<.0001 && abs(x2+1.75)<.0001
       dbDeleteObject(s) rect(cv "Metal1" -1.81 .50 -1.75 .97))
   ))
 rect(cv "Metal1" -1.235 .23 -1.105 .35)
 rect(cv "Metal1" -1.235 1.125 -1.105 1.245)
 rect(cv "Metal1" -.71 .23 -.59 .35)
 rect(cv "Metal1" -.71 1.125 -.59 1.245)
 when(pdWidth<200e-9
  foreach(s cv~>shapes when(s~>layerName=="Nimp" && abs(caar(s~>bBox)+1.07)<.0001 dbDeleteObject(s)))
  rect(cv "Nimp" -1.53 .13 -.55 .45))
 ; Both width variants use the same compact routing floorplan.
 rect(cv "Poly" -1.32 .335 -1.275 1.045)
 rect(cv "Poly" -.805 .335 -.76 1.06)
 gateContact(cv -1.30 .775 .69 .89)
 via12compact(cv -.83 .775 nil)
 rect(cv "Metal2" -1.365 .735 -.765 .815)
 gateContact(cv -.78 .96 .825 1.025)
 via12compact(cv -1.04 .96 nil)
 rect(cv "Metal2" -1.105 .92 -.715 1.0)
 ; Wordline: vertical poly gate leads, horizontal Metal2 outside the cell core.
 rect(cv "Poly" -1.905 -.125 -1.86 .10)
 rect(cv "Poly" -.26 -.125 -.215 .10)
 gateContact(cv -1.885 -.125 -.225 -.025)
 gateContact(cv -.24 -.125 -.225 -.025)
 rect(cv "Metal2" -1.95 -.165 -.175 -.085)
 ; Standalone well and substrate taps, tucked into the empty left-side spaces.
 rect(cv "Nwell" -1.90 1.005 -.56 1.43)
 rect(cv "Oxide" -1.80 1.10 -1.60 1.30)
 rect(cv "Nimp" -1.86 1.04 -1.54 1.36)
 rect(cv "Cont" -1.73 1.17 -1.67 1.23)
 rect(cv "Metal1" -1.74 1.135 -1.66 1.42)
 rect(cv "Oxide" -1.80 .13 -1.60 .33)
 rect(cv "Pimp" -1.86 .07 -1.54 .39)
 rect(cv "Cont" -1.73 .20 -1.67 .26)
 rect(cv "Metal1" -1.74 .11 -1.66 .30)
 ; Seven schematic-compatible ports; observation pins do not add circuit loads.
 port(cv "Vdd" "Metal1" -1.70 1.36 -1.48 1.42)
 port(cv "GND" "Metal1" -1.50 .11 -1.28 .17)
 port(cv "BL_bar" "Metal1" -2.035 .51 -1.94 .65)
 port(cv "BL" "Metal1" -.18 .835 -.085 .985)
 port(cv "Q_bar" "Metal1" -1.80 .91 -1.60 .97)
 port(cv "Q" "Metal1" -.60 .75 -.40 .81)
 port(cv "WL" "Metal2" -1.15 -.165 -.95 -.085)
 rect(cv "prBoundary" -2.12 -.23 0.0 1.45)
 ; Put the boundary origin at (0,0).
 foreach(s cv~>shapes dbMoveFig(s cv list(list(2.12 .23) "R0" 1.0)))
 foreach(i cv~>instances dbMoveFig(i cv list(list(2.12 .23) "R0" 1.0)))
 dbSave(cv) printf("COMPACT_LAYOUT %s %L\n" cellName cv~>bBox) dbClose(cv)
 ))
buildCompact("sram_cell" 360e-9 240e-9)
buildCompact("sram_cell_default" 120e-9 120e-9)
exit()
