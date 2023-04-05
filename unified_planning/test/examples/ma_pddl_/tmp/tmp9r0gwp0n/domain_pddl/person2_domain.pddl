(define (domain ma_taxi-domain)
 (:requirements :factored-privacy :typing)
 (:types location taxi ag - object
    person1_type person2_type taxi1_type taxi2_type - ag
 )
 (:predicates
  (free ?location - location)
  (directly_connected ?l1 - location ?l2 - location)
  (at_ ?taxi - taxi ?location - location)
  (empty ?taxi - taxi)
  (:private
   (a_goal_of ?agent - ag ?location - location)
   (a_in ?agent - ag ?taxi - taxi)
   (a_pos ?agent - ag ?location - location)
   (a_we ?agent - ag ?taxi - taxi)))
 (:action enter_p
  :parameters ( ?person2 - person2_type ?t - taxi ?l - location)
  :precondition (and 
   (a_pos ?person2 ?l)
   (at_ ?t ?l)
   (empty ?t)
  )
  :effect (and
   (not (empty ?t))
   (not (a_pos ?person2 ?l))
   (a_in ?person2 ?t)
))
 (:action exit_p
  :parameters ( ?person2 - person2_type ?t - taxi ?l - location)
  :precondition (and 
   (a_in ?person2 ?t)
   (at_ ?t ?l)
   (a_goal_of ?person2 ?l)
  )
  :effect (and
   (not (a_in ?person2 ?t))
   (empty ?t)
   (a_pos ?person2 ?l)
))
)
