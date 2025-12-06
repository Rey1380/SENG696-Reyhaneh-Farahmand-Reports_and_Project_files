package masproject;

import jade.core.Agent;

public class TestAgent extends Agent {
    @Override
    protected void setup() {
        System.out.println("TestAgent started! My AID is: " + getAID().getName());
    }
}
