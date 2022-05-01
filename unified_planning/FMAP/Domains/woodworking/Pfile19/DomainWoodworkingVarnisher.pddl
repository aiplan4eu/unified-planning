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
(:action do-immersion-varnish
  :parameters (?x - part ?m - immersion-varnisher
               ?newcolour - acolour ?surface - surface ?c - acolour)
  :precondition (and
          (available ?x)
          (has-colour ?m ?newcolour)
          (= (surface-condition ?x) ?surface)
          (is-smooth ?surface)
          (= (treatment ?x) untreated) (= (colour ?x) ?c))
  :effect (and
          (assign (treatment ?x) varnished)
          (assign (colour ?x) ?newcolour)))
(:action do-spray-varnish
  :parameters (?x - part ?m - spray-varnisher
               ?newcolour - acolour ?surface - surface)
  :precondition (and
          (available ?x)
          (has-colour ?m ?newcolour)
          (= (surface-condition ?x) ?surface)
          (is-smooth ?surface)
          (= (treatment ?x) untreated))
  :effect (and
          (assign (treatment ?x) varnished)
          (assign (colour ?x) ?newcolour)))
(:action do-glaze
  :parameters (?x - part ?m - glazer ?newcolour - acolour)
  :precondition (and
          (available ?x)
          (has-colour ?m ?newcolour)
          (= (treatment ?x) untreated))
  :effect (and
          (assign (treatment ?x) glazed)
          (assign (colour ?x) ?newcolour))))
