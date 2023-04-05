(define (domain p_g-domain)
 (:requirements :factored-privacy :typing)
 (:types location postureg stateg modeg pouchobj scale_a_type mark10_a_type robot_a_type)
 (:constants
   pouch1 pouch2 - pouchobj
   scale - location
 )
 (:predicates
   (:private
   (a_restloc ?agent - scale_a_type ?x - location ?device - location)))
 (:action measure_scale_scalerest_pouch1_0
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (pouchat pouch1 scale)
   (reset scale)
  )
  :effect (and
   (measuredat pouch1 scale)
   (not (reset scale))
))
 (:action measure_scale_scalerest_pouch2_0
  :parameters ( ?scale_a - scale_a_type)
  :precondition (and 
   (pouchat pouch2 scale)
   (reset scale)
  )
  :effect (and
   (measuredat pouch2 scale)
   (not (reset scale))
))
)
