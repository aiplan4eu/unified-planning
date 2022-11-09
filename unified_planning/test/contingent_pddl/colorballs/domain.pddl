
(define (domain colorballs)

   (:requirements :strips :typing :contingent)
   (:types pos obj col gar)
   (:predicates (color ?o ?c) (trashed ?o) (garbage-color ?t ?c) (garbage-at ?t ?p)
                (adj ?i ?j)  (at ?i) (holding ?o) (obj-at ?o ?i) )

   (:action observe-color
     :parameters (?c - col ?o - obj)
     :precondition (holding ?o)
     :observe (color ?o ?c)
   )

   (:action observe-ball
      :parameters (?pos - pos ?o - obj)
      :precondition (at ?pos)
      :observe (obj-at ?o ?pos))

   (:action move
      :parameters (?i - pos ?j - pos )
      :precondition (and (adj ?i ?j) (at ?i))
      :effect (and (not (at ?i)) (at ?j)))

   (:action pickup
      :parameters (?o - obj ?i - pos)
      :precondition (and (at ?i) (obj-at ?o ?i))
      :effect (and (holding ?o) (not (obj-at ?o ?i))))

   (:action trash
      :parameters (?o - obj ?c - col ?t - gar ?p - pos)
      :precondition (and (color ?o ?c) (holding ?o) (garbage-at ?t ?p) (at ?p))
      :effect (when (garbage-color ?t ?c) (trashed ?o) )
      )
)
