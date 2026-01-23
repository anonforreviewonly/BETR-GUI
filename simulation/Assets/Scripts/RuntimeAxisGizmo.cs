using UnityEngine;

[ExecuteAlways]
public class RuntimeAxisGizmo : MonoBehaviour
{
    [Header("Appearance")]
    public float axisLength = 1.0f;
    public float coneLength = 0.15f;
    public float coneRadius = 0.06f;
    [Tooltip("Screen-space pixel offset for the letters from the cone tips.")]
    public Vector2 labelOffset = new Vector2(10, -8);
    public int coneSegments = 24;
    public bool depthTest = true;     // if false, axes render on top of everything

    [Header("Cameras")]
    public Camera targetCamera;        // leave null to draw for all cameras

    static Mesh s_ConeMesh;
    static Material s_GLMaterial;

    void OnEnable()
    {
        if (s_GLMaterial == null)
        {
            // Simple colored material suitable for GL immediate-mode
            var shader = Shader.Find("Hidden/Internal-Colored");
            s_GLMaterial = new Material(shader)
            {
                hideFlags = HideFlags.HideAndDontSave
            };
            // Enable alpha blending, disable backface culling, set ZTest later per flag
            s_GLMaterial.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            s_GLMaterial.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            s_GLMaterial.SetInt("_Cull", (int)UnityEngine.Rendering.CullMode.Off);
            s_GLMaterial.SetInt("_ZWrite", 0);
        }
    
        if (s_ConeMesh == null)
            s_ConeMesh = BuildCone(coneSegments);
    }

    void OnDisable()
    {
        // Keep static caches alive; Unity cleans up on domain reloads.
    }

    // Draw lines and cones in the camera render
    void OnRenderObject()
    {
        if (targetCamera != null && Camera.current != targetCamera) return;

        if (s_GLMaterial == null) return;

        s_GLMaterial.SetInt("_ZTest", depthTest
            ? (int)UnityEngine.Rendering.CompareFunction.LessEqual
            : (int)UnityEngine.Rendering.CompareFunction.Always);

        s_GLMaterial.SetPass(0);

        var p = transform.position;
        var r = transform.rotation;

        // Local axes in world space
        Vector3 xDir = r * Vector3.forward;
        Vector3 yDir = r * Vector3.left;
        Vector3 zDir = r * Vector3.up;

        Vector3 xTip = p + xDir * axisLength;
        Vector3 yTip = p + yDir * axisLength;
        Vector3 zTip = p + zDir * axisLength;

        // Draw axis lines (GL lines are 1px; for thickness you'd draw camera-facing quads)
        GL.Begin(GL.LINES);

        GL.Color(Color.black); GL.Vertex(p);
        GL.Color(Color.black); GL.Vertex(xTip);

        GL.Color(Color.black); GL.Vertex(p);
        GL.Color(Color.black); GL.Vertex(yTip);

        GL.Color(Color.black); GL.Vertex(p);
        GL.Color(Color.black); GL.Vertex(zTip);

        GL.End();

        // Draw cones at tips. Cone mesh points along +Z in its local space.
        if (s_ConeMesh == null) s_ConeMesh = BuildCone(coneSegments);

        DrawConeAt(xTip, Quaternion.FromToRotation(Vector3.forward, xDir), Color.red);
        DrawConeAt(yTip, Quaternion.FromToRotation(Vector3.forward, yDir), Color.green);
        DrawConeAt(zTip, Quaternion.FromToRotation(Vector3.forward, zDir), Color.blue);
    }

    // Overlay labels in screen space
    void OnGUI()
    {
        var cam = targetCamera != null ? targetCamera
                : (Camera.main != null ? Camera.main : null);
        if (cam == null) return;

        var p = transform.position;
        var r = transform.rotation;

        DrawLabel(cam, p + r * Vector3.forward * axisLength, "X", Color.red);
        DrawLabel(cam, p + r * Vector3.left    * axisLength, "Y", Color.green);
        DrawLabel(cam, p + r * Vector3.up * axisLength, "Z", Color.blue);
    }

    void DrawLabel(Camera cam, Vector3 worldPos, string text, Color color)
    {
        Vector3 sp = cam.WorldToScreenPoint(worldPos);
        if (sp.z < 0f) return; // behind camera

        // Convert to GUI space (top-left origin)
        Vector2 guiPos = new Vector2(sp.x, Screen.height - sp.y) + labelOffset;

        var style = new GUIStyle(GUI.skin.label)
        {
            fontStyle = FontStyle.Bold,
            normal = { textColor = color }
        };

        // Small outline for readability
        var shadow = new GUIStyle(style);
        shadow.normal.textColor = new Color(0, 0, 0, 0.65f);

        Rect r = new Rect(guiPos.x, guiPos.y, 100, 20);
        GUI.Label(new Rect(r.x + 1, r.y + 1, r.width, r.height), text, shadow);
        GUI.Label(r, text, style);
    }

    void DrawConeAt(Vector3 pos, Quaternion rot, Color color)
    {
        if (s_GLMaterial == null || s_ConeMesh == null) return;

        s_GLMaterial.SetColor("_Color", color);
        s_GLMaterial.SetPass(0);

        // Scale so cone length is along local +Z
        Matrix4x4 m = Matrix4x4.TRS(pos, rot, new Vector3(coneRadius, coneRadius, coneLength));
        Graphics.DrawMeshNow(s_ConeMesh, m);
    }

    // Generates a unit cone aligned along +Z with base at z=0 and tip at z=1
    Mesh BuildCone(int segments)
    {
        segments = Mathf.Max(8, segments);

        var mesh = new Mesh();
        int vertCount = segments + 2; // ring + center + tip
        Vector3[] v = new Vector3[vertCount];
        Vector3 tip = new Vector3(0, 0, 1);
        Vector3 center = Vector3.zero;

        // Ring vertices on unit circle in XY at z=0
        for (int i = 0; i < segments; i++)
        {
            float a = (i / (float)segments) * Mathf.PI * 2f;
            v[i] = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f);
        }
        v[segments] = center; // base center
        v[segments + 1] = tip; // tip

        // Triangles: side surface (segments * 3) and base (segments * 3)
        int[] tris = new int[segments * 3 * 2];

        int t = 0;
        // Side
        for (int i = 0; i < segments; i++)
        {
            int i0 = i;
            int i1 = (i + 1) % segments;
            int iTip = segments + 1;

            tris[t++] = i0; tris[t++] = i1; tris[t++] = iTip;
        }
        // Base (clockwise so it faces -Z; we disabled culling anyway)
        for (int i = 0; i < segments; i++)
        {
            int i0 = i;
            int i1 = (i + 1) % segments;
            int iCenter = segments;

            tris[t++] = iCenter; tris[t++] = i1; tris[t++] = i0;
        }

        mesh.vertices = v;
        mesh.triangles = tris;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        mesh.name = "RuntimeCone(+Z)";

        return mesh;
    }
}
