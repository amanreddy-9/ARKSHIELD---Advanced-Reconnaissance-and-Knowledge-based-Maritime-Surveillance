"""Conservative background-flow camera compensation and multi-signal shot isolation.
Cloud-like bright neutral coverage suppresses cut resets; uncertain motion is not applied.
This module does not perform cross-shot appearance re-identification.
"""
import cv2
import numpy as np


class CameraMotionEstimator:
    def __init__(self,max_width=640,min_inliers=20):
        self.max_width=max_width;self.min_inliers=min_inliers;self.reset()

    def reset(self):
        self.previous=None;self.previous_mask=None;self.previous_hist=None;self.previous_cloud=0.

    def exclude_current_boxes(self,boxes,image_width):
        """Refine next frame's background mask using actual current detections."""
        if self.previous_mask is None:return
        scale=self.previous_mask.shape[1]/image_width
        for box in boxes:
            x1,y1,x2,y2=[int(v*scale) for v in box]
            x1=max(0,x1-10);y1=max(0,y1-10)
            x2=min(self.previous_mask.shape[1],x2+10);y2=min(self.previous_mask.shape[0],y2+10)
            if x2>x1 and y2>y1:self.previous_mask[y1:y2,x1:x2]=0

    def update(self,frame,boxes=()):
        h,w=frame.shape[:2];scale=min(1.,self.max_width/max(h,w))
        small=cv2.resize(frame,(round(w*scale),round(h*scale)))
        gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
        mask=np.full(gray.shape,255,np.uint8)
        for box in boxes:
            x1,y1,x2,y2=[int(v*scale) for v in box];pad=10
            x1=max(0,x1-pad);y1=max(0,y1-pad);x2=min(gray.shape[1],x2+pad);y2=min(gray.shape[0],y2+pad)
            if x2>x1 and y2>y1:mask[y1:y2,x1:x2]=0
        hist=cv2.calcHist([small],[0,1,2],None,[8,8,8],[0,256]*3)
        cv2.normalize(hist,hist,norm_type=cv2.NORM_L1)
        bright_neutral=(small.max(2)-small.min(2)<35)&(gray>170)
        # Cloud and foam features are moving occluders, not stable camera landmarks.
        moving_mask=cv2.dilate(bright_neutral.astype(np.uint8),np.ones((9,9),np.uint8))>0
        mask[moving_mask]=0
        cloud=float(np.mean((small.max(2)-small.min(2)<35)&(gray>170)))
        result={'affine':None,'scene_cut':False,'status':'initial_frame','inliers':0,'inlier_ratio':0.,'appearance_delta':0.,'histogram_distance':0.}
        if self.previous is not None and self.previous.shape==gray.shape:
            diff=float(np.mean(cv2.absdiff(self.previous,gray)))/255
            hist_dist=float(cv2.compareHist(self.previous_hist,hist,cv2.HISTCMP_BHATTACHARYYA))
            points=cv2.goodFeaturesToTrack(self.previous,400,.015,8,mask=self.previous_mask)
            valid=False;matrix=None;ratio=0.;count=0
            if points is not None and len(points)>=self.min_inliers:
                next_pts,status,_=cv2.calcOpticalFlowPyrLK(self.previous,gray,points,None,winSize=(21,21),maxLevel=3)
                if next_pts is not None:
                    back,back_status,_=cv2.calcOpticalFlowPyrLK(gray,self.previous,next_pts,None,winSize=(21,21),maxLevel=3)
                    if back is not None:
                        good=(status.ravel()==1)&(back_status.ravel()==1)&(np.linalg.norm(points-back,axis=2).ravel()<1.5)
                        p=points.reshape(-1,2)[good];q=next_pts.reshape(-1,2)[good]
                        inside=(q[:,0]>=0)&(q[:,0]<gray.shape[1])&(q[:,1]>=0)&(q[:,1]<gray.shape[0])
                        p=p[inside];q=q[inside]
                        if len(q):
                            keep=mask[q[:,1].astype(int),q[:,0].astype(int)]>0;p=p[keep];q=q[keep]
                        if len(p)>=self.min_inliers:
                            matrix,inliers=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=2.,maxIters=1000,confidence=.99)
                            if matrix is not None and inliers is not None:
                                inliers=inliers.ravel().astype(bool);count=int(inliers.sum());ratio=count/max(1,len(points))
                                mscale=float(np.linalg.norm(matrix[0,:2]));angle=abs(np.degrees(np.arctan2(matrix[1,0],matrix[0,0])))
                                spread=np.ptp(p[inliers],axis=0) if count else np.zeros(2)
                                valid=(np.isfinite(matrix).all() and count>=self.min_inliers and ratio>=.25
                                       and count/len(p)>=.65 and .75<=mscale<=1.33 and angle<=25
                                       and np.linalg.norm(matrix[:,2])<.25*max(gray.shape)
                                       and np.all(spread>np.array([gray.shape[1],gray.shape[0]])*.25))
            clouds_present=max(cloud,self.previous_cloud)>.25
            if max(cloud,self.previous_cloud)>.08:
                valid=False  # Moving cloud banks must not drive global camera control.
            # Abrupt appearance change + failed geometric continuity, not histogram alone.
            cut=not valid and not clouds_present and ((diff>.22 and hist_dist>.35) or (diff>.30 and ratio<.15) or (diff>.07 and hist_dist>.45 and ratio<.10))
            if valid:
                aligned=cv2.warpAffine(self.previous,matrix,(gray.shape[1],gray.shape[0]))
                support=cv2.warpAffine(self.previous_mask,matrix,(gray.shape[1],gray.shape[0]))>0
                support &= mask>0
                if support.any():
                    residual=float(np.mean(cv2.absdiff(aligned,gray)[support]))/255
                    if residual>.20:
                        valid=False;cut=not clouds_present and hist_dist>.35
            result.update(scene_cut=bool(cut),status='scene_cut' if cut else 'compensated' if valid else 'cloud_or_low_confidence' if clouds_present else 'insufficient_background',
                          inliers=count,inlier_ratio=ratio,appearance_delta=diff,histogram_distance=hist_dist)
            if valid:
                matrix=matrix.copy();matrix[:,2]/=scale;result['affine']=matrix
        elif self.previous is not None:
            result.update(scene_cut=True,status='resolution_changed')
        self.previous=gray;self.previous_mask=mask;self.previous_hist=hist;self.previous_cloud=cloud
        return result
