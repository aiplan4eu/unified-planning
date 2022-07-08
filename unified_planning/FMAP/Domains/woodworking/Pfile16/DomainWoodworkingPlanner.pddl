(define (domain woodworking)
(:requirements :typing :equality :fluents)
(:types
    acolour awood woodobj machine
    surface treatmentstatus
    aboardsize apartsize - object
    highspeed-saw glazer grinder immersion-varnisher
    planer saw spray-varnisher - machine
    board part - woodobj)
(:constants
            verysmooth smooth rough - surface
            varnished glazed untreated colourfragments - treatmentstatus
            natural - acolour
            small medium large - apartsize
            unknown-wood - awood
            no-board - board)
(:predicates
          (unused ?obj - part)
          (available ?obj - woodobj)
          (empty ?m - highspeed-saw)
          (has-colour ?machine - machine ?colour - acolour)
          (is-smooth ?surface - surface))
(:functions
          (surface-condition ?obj - woodobj) - surface
          (treatment ?obj - part) - treatmentstatus
          (colour ?obj - part) - acolour
          (wood ?obj - woodobj) - awood
          (boardsize ?board - board) - aboardsize
          (goalsize ?part - part) - apartsize
          (boardsize-successor ?size1 - aboardsize) - aboardsize
          (in-highspeed-saw ?m - highspeed-saw) - board
          (grind-treatment-change ?old - treatmentstatus) - treatmentstatus)
(:action do-plane
  :parameters (?x - part ?m - planer ?oldsurface - surface
               ?oldcolour - acolour ?oldtreatment - treatmentstatus)
  :precondition (and
          (available ?x)
          (= (surface-condition ?x) ?oldsurface)
          (= (treatment ?x) ?oldtreatment)
          (= (colour ?x) ?oldcolour))
  :effect (and
          (assign (surface-condition ?x) smooth)
          (assign (treatment ?x) untreated)
          (assign (colour ?x) natural))))
