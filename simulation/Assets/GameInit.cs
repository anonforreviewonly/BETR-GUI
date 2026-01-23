using UnityEngine;

public class GameInit : MonoBehaviour
{
    public static bool LOADED;
    public GameObject manager;
    public Camera mainCamera;
    void Start()
    {
        if (!LOADED)
        {
            Instantiate(manager);
            Instantiate(mainCamera);
            LOADED = true;
        }
    }

   
}
