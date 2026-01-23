using UnityEngine;

public class Detector : MonoBehaviour
{
    public bool objectDetected = false;
    public GameObject collidedWith;
    public string collidedWithName = "";

    private void OnTriggerEnter(Collider other)
    {
       EnterStay(other);
    }

    private void OnTriggerStay(Collider other)
    {
        EnterStay(other);
    }
    
    private void OnTriggerExit(Collider other)
    {
        Exit();
    }
    
    private void OnCollisionEnter(Collision other)
    {
        EnterStay(other.collider);
    }

    private void OnCollisionStay(Collision other)
    {
        EnterStay(other.collider);
    }

    private void OnCollisionExit(Collision other)
    {
        Exit();
    }

    private void EnterStay(Collider other)
    {
        objectDetected = !other.gameObject.CompareTag("Player") && !other.gameObject.CompareTag("robot") && !other.gameObject.CompareTag("Terrain");
        if (objectDetected)
        {
            collidedWith = other.gameObject;
            collidedWithName = collidedWith.name;
        }
    }

    private void Exit()
    {
        objectDetected = false;
        collidedWithName = "";
        collidedWith = null;
    }
}