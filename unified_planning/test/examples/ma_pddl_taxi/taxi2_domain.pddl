(define (domain ma_taxi-domain)
 (:requirements :factored-privacy :typing)
 (:types location taxi person1_type person2_type taxi1_type taxi2_type)
 (:predicates
 (free ?location - location)
  (directly_connected ?l1 - location ?l2 - location)
  (at_ ?taxi - taxi ?location - location)
  (empty ?taxi - taxi)
(a_pos ?agent - person1_type ?location - location)
  (a_pos ?agent - person2_type ?location - location)
  (:private
   (a_in ?agent - taxi2_type ?taxi - taxi)
   (a_driving ?agent - taxi2_type ?taxi - taxi)))
 (:action drive_t
  :parameters ( ?taxi2 - taxi2_type ?t - taxi ?from_ - location ?to - location)
  :precondition (and 
   (at_ ?t ?from_)
   (directly_connected ?from_ ?to)
   (free ?to)
  )
  :effect (and
   (not (at_ ?t ?from_))
   (not (free ?to))
   (at_ ?t ?to)
   (free ?from_)
))
)
