(define (problem p_g-problem)
 (:domain p_g-domain)
 (:objects
   home drawer pouchposedrawer vision2 pickup bin binup scale scalerest scaleout pouchposescale scaleup mark10 mark10rest mark10out mark10up pouchposemark10 - location
   default grasping open20 open0 - postureg
   startstate active - stateg
   horizontal vertical - modeg
   pouch1 pouch2 pouch3 - pouchobj
   robot_a - robot_a_type
 )
 (:init
  (restloc scalerest scale)
  (restloc mark10rest mark10)
  (droppos vision2 drawer)
  (droppos scaleup scale)
  (droppos mark10up mark10)
  (droppos binup bin)
  (grasppos pouchposedrawer drawer)
  (grasppos pouchposescale scale)
  (grasppos pouchposemark10 mark10)
  (exitpos pickup drawer)
  (exitpos scaleout scale)
  (exitpos mark10out mark10))
 (:goal (and (measuredat pouch1 scale) (measuredat pouch1 mark10) (pouchat pouch1 bin) (measuredat pouch2 scale) (measuredat pouch2 mark10) (pouchat pouch2 bin)))
)
