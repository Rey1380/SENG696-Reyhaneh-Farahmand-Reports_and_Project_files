package masproject;

import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

import org.json.JSONObject;

public class SeverityAgent extends Agent {

    @Override
    protected void setup() {
        System.out.println("SeverityAgent started: " + getAID().getName());

        addBehaviour(new CyclicBehaviour() {
            @Override
            public void action() {
                ACLMessage msg = receive();
                if (msg == null) {
                    block();
                    return;
                }

                try {
                    JSONObject input = new JSONObject(msg.getContent());
                    String file = input.getString("file");
                    String code = input.getString("code");
                    int aiLabel = input.getInt("ai_label");

                    JSONObject sevReq = new JSONObject();
                    sevReq.put("file", file);
                    sevReq.put("code", code);
                    sevReq.put("ai_label", aiLabel);

                    String response = callSeverityAPI(sevReq);
                    System.out.println("[SeverityAgent] → Sent triage result");

                    ACLMessage reply = msg.createReply();
                    reply.setPerformative(ACLMessage.INFORM);
                    reply.setContent(response);
                    send(reply);

                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }


    private String callSeverityAPI(JSONObject obj) throws Exception {
        URL url = new URL("http://127.0.0.1:8082/severity");
        HttpURLConnection con = (HttpURLConnection) url.openConnection();

        con.setRequestMethod("POST");
        con.setRequestProperty("Content-Type", "application/json");
        con.setDoOutput(true);

        try (OutputStream os = con.getOutputStream()) {
            os.write(obj.toString().getBytes());
        }

        BufferedReader br = new BufferedReader(new InputStreamReader(con.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;

        while ((line = br.readLine()) != null) sb.append(line);

        return sb.toString();
    }
}
