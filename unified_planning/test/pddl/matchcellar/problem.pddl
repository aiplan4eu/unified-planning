(define (problem p3)
 (:domain matchcellar)
 (:objects
    match0 match1 match2 - match
    fuse0 fuse1 fuse2 - fuse
)
 (:init
  (handfree)
  (unused match0)
  (unused match1)
  (unused match2)
)
 (:goal
  (and
     (mended fuse0)
     (mended fuse1)
     (mended fuse2)
))
)
