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
(:action load-highspeed-saw
  :parameters (?b - board ?m - highspeed-saw)
  :precondition (and
          (= (in-highspeed-saw ?m) no-board)
          (available ?b))
  :effect (and
          (not (available ?b))
          (assign (in-highspeed-saw ?m) ?b)))
(:action unload-highspeed-saw
  :parameters (?b - board ?m - highspeed-saw)
  :precondition (= (in-highspeed-saw ?m) ?b)
  :effect (and
          (available ?b)
          (assign (in-highspeed-saw ?m) no-board)))
(:action cut-board-small
  :parameters (?b - board ?p - part ?m - highspeed-saw ?w - awood
               ?surface - surface ?size_before ?size_after - aboardsize)
  :precondition (and
          (unused ?p)
          (= (goalsize ?p) small)
          (= (in-highspeed-saw ?m) ?b)
          (= (wood ?b) ?w)
          (= (surface-condition ?b) ?surface)
          (= (boardsize ?b) ?size_before)
          (= (boardsize-successor ?size_after) ?size_before))
  :effect (and
          (not (unused ?p))
          (available ?p)
          (assign (wood ?p) ?w)
          (assign (surface-condition ?p) ?surface)
          (assign (colour ?p) natural)
          (assign (treatment ?p) untreated)
          (assign (boardsize ?b) ?size_after)))
(:action cut-board-medium
  :parameters (?b - board ?p - part ?m - highspeed-saw ?w - awood
               ?surface - surface
               ?size_before ?s1 ?size_after - aboardsize)
  :precondition (and (unused ?p) (= (goalsize ?p) medium)
                     (= (in-highspeed-saw ?m) ?b)
                     (= (wood ?b) ?w)
                     (= (surface-condition ?b) ?surface)
                     (= (boardsize ?b) ?size_before)
                     (= (boardsize-successor ?size_after) ?s1)
                     (= (boardsize-successor ?s1) ?size_before))
  :effect (and (not (unused ?p)) (available ?p)
               (assign (wood ?p) ?w)
               (assign (surface-condition ?p) ?surface)
               (assign (colour ?p) natural)
               (assign (treatment ?p) untreated)
               (assign (boardsize ?b) ?size_after)))
 (:action cut-board-large
  :parameters (?b - board ?p - part ?m - highspeed-saw ?w - awood
               ?surface - surface
               ?size_before ?s1 ?s2 ?size_after - aboardsize)
  :precondition (and (unused ?p) (= (goalsize ?p) large)
                     (= (in-highspeed-saw ?m) ?b)
                     (= (wood ?b) ?w)
                     (= (surface-condition ?b) ?surface)
                     (= (boardsize ?b) ?size_before)
                     (= (boardsize-successor ?size_after) ?s1)
                     (= (boardsize-successor ?s1) ?s2)
                     (= (boardsize-successor ?s2) ?size_before))
  :effect (and (not (unused ?p)) (available ?p)
               (assign (wood ?p) ?w)
               (assign (surface-condition ?p) ?surface)
               (assign (colour ?p) natural)
               (assign (treatment ?p) untreated)
               (assign (boardsize ?b) ?size_after)))
(:action do-saw-small
  :parameters (?b - board ?p - part ?m - saw ?w - awood
               ?surface - surface ?size_before ?size_after - aboardsize)
  :precondition (and (unused ?p) (= (goalsize ?p) small)
                     (available ?b) (= (wood ?b) ?w)
                     (= (surface-condition ?b) ?surface)
                     (= (boardsize ?b) ?size_before)
                     (= (boardsize-successor ?size_after) ?size_before))
  :effect (and (not (unused ?p)) (available ?p)
               (assign (wood ?p) ?w) (assign (surface-condition ?p) ?surface)
               (assign (colour ?p) natural)
               (assign (treatment ?p) untreated)
               (assign (boardsize ?b) ?size_after)))
(:action do-saw-medium
  :parameters (?b - board ?p - part ?m - saw ?w - awood
               ?surface - surface
               ?size_before ?s1 ?size_after - aboardsize)
  :precondition (and (unused ?p) (= (goalsize ?p) medium)
                     (available ?b) (= (wood ?b) ?w)
                     (= (surface-condition ?b) ?surface)
                     (= (boardsize ?b) ?size_before)
                     (= (boardsize-successor ?size_after) ?s1)
                     (= (boardsize-successor ?s1) ?size_before))
  :effect (and (not (unused ?p)) (available ?p)
               (assign (wood ?p) ?w)
               (assign (surface-condition ?p) ?surface)
               (assign (colour ?p) natural)
               (assign (treatment ?p) untreated)
               (assign (boardsize ?b) ?size_after)))
(:action do-saw-large
  :parameters (?b - board ?p - part ?m - saw ?w - awood
               ?surface - surface
               ?size_before ?s1 ?s2 ?size_after - aboardsize)
  :precondition (and (unused ?p)    (= (goalsize ?p) large)
                     (available ?b) (= (wood ?b) ?w)
                     (= (surface-condition ?b) ?surface)
                     (= (boardsize ?b) ?size_before)
                     (= (boardsize-successor ?size_after) ?s1)
                     (= (boardsize-successor ?s1) ?s2)
                     (= (boardsize-successor ?s2) ?size_before))
  :effect (and (not (unused ?p)) (available ?p)
               (assign (wood ?p) ?w)
               (assign (surface-condition ?p) ?surface)
               (assign (colour ?p) natural)
               (assign (treatment ?p) untreated)
               (assign (boardsize ?b) ?size_after))))
